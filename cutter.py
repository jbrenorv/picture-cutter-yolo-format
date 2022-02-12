from glob import glob
from PIL import Image
from shapely.geometry import Polygon
import pandas as pd
import argparse
import shutil
import os

from utils import Rectangle, get_hood_approximate_height, log, progressBar


def get_txt_name(image_name):
    '''
    Retorna o nome do .txt de uma dada imagem
    '''

    split = image_name.split('.')
    split[-1] = 'txt'
    return '.'.join(split)


def get_txt_path(image_path):
    '''
    Retorna o caminho original para o .txt correspondente uma dada imagem
    '''

    image_name = os.path.basename(image_path)
    txt_name = get_txt_name(image_name)
    return os.path.join(os.path.dirname(image_path), txt_name)


def get_cropped_image_rectangle(original_image_size, hood_approximate_height, width, height):
    '''
    Define a regiao de corte
    '''

    # altura media do capo
    # hood_approximate_height = 200

    x_min = max(0, (original_image_size[0] // 2) - (width // 2))
    x_max = min(original_image_size[0], x_min + width)
    y_max = max(0, original_image_size[1] - hood_approximate_height)
    y_min = max(0, y_max - height)

    return Rectangle(x_min, y_min, x_max, y_max)


def cut(cropped_image_rectangle: Rectangle, image: Image, output_image_path):
    '''
    Corta uma imagem
    '''

    x_min, y_min, x_max, y_max = cropped_image_rectangle.describe()

    cropped_image = image.crop((x_min, y_min, x_max, y_max,))
    cropped_image.save(output_image_path)


def generate_txt(input_txt_path: str, output_txt_path: str, cropped_image_rectangle: Rectangle,
                 original_image_size):
    '''
    Gera o txt da imagem cortada, com base no txt da imagem original
    '''

    try:
        labels = pd.read_csv(input_txt_path, sep=' ',
                             names=['class', 'x', 'y', 'w', 'h'])
    except:
        print(f"(Aviso): Nao foi possivel abrir {input_txt_path}")
        return False

    original_image_width, original_image_height = original_image_size

    # reescalando valores
    labels[['x', 'w']] = labels[['x', 'w']] * original_image_width
    labels[['y', 'h']] = labels[['y', 'h']] * original_image_height

    cropped_image_width = cropped_image_rectangle.x_max - cropped_image_rectangle.x_min
    cropped_image_height = cropped_image_rectangle.y_max - cropped_image_rectangle.y_min
    cropped_image_pol = Polygon([
        (cropped_image_rectangle.x_min, cropped_image_rectangle.y_min),
        (cropped_image_rectangle.x_max, cropped_image_rectangle.y_min),
        (cropped_image_rectangle.x_max, cropped_image_rectangle.y_max),
        (cropped_image_rectangle.x_min, cropped_image_rectangle.y_max)])

    txt_rows = []
    boxes = []

    for row in labels.iterrows():
        x1 = row[1]['x'] - row[1]['w']/2
        y1 = row[1]['y'] - row[1]['h']/2
        x2 = row[1]['x'] + row[1]['w']/2
        y2 = row[1]['y'] + row[1]['h']/2

        boxes.append((int(row[1]['class']), Polygon(
            [(x1, y1), (x2, y1), (x2, y2), (x1, y2)])))

    for box in boxes:
        if cropped_image_pol.intersects(box[1]):
            inter = cropped_image_pol.intersection(box[1])
            new_box = inter.envelope

            # obtendo o novo centro do bounding box
            centre = new_box.centroid

            # obtendo as coordenadas dos vertices do poligono
            x, y = new_box.exterior.coords.xy

            # YOLO normalizacao para a nova largura e altura
            new_width = (max(x) - min(x)) / cropped_image_width
            new_height = (max(y) - min(y)) / cropped_image_height

            # YOLO normalizacao para as coordenadas do novo centro
            new_x = (
                centre.coords.xy[0][0] - cropped_image_rectangle.x_min) / cropped_image_width
            new_y = (
                centre.coords.xy[1][0] - cropped_image_rectangle.y_min) / cropped_image_height

            txt_rows.append([box[0], new_x, new_y, new_width, new_height])

    if len(txt_rows) > 0:
        txts_df = pd.DataFrame(txt_rows,
                               columns=['class', 'x', 'y', 'w', 'h'])
        txts_df.to_csv(output_txt_path, sep=' ', index=False,
                       header=False, float_format='%.6f')

        return True

    # print(f"(Aviso): Sem conteudo para {input_txt_path}")

    return False


def create_dir_if_not_exists(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-width", type=int, default=1500,
                        help="A largura das novas imagens. Dafault: 1500")
    parser.add_argument("-height", type=int, default=580,
                        help="A altura das novas imagens. Dafault: 580")
    parser.add_argument("-input_path", required=True,
                        help="Caminho para as imagens")

    args = parser.parse_args()

    classes_file_name = "classes.txt"
    ces_pattern_path = os.path.join(args.input_path, 'CE*')
    ce_paths = glob(ces_pattern_path)

    for ce_path in ce_paths:

        capos_pttrn = os.path.join(ce_path, "rotuladas/*")
        capos = [os.path.basename(c) for c in glob(capos_pttrn)]

        if classes_file_name in capos:
            capos.remove(classes_file_name)
            shutil.copyfile(os.path.join(ce_path, f"rotuladas/{classes_file_name}"),
                            os.path.join(ce_path, f"rotuladas_cortadas/{classes_file_name}"))

        part = 1
        images_per_part = 50
        count = 0
        total_saved = 0
        current_part_path = os.path.join(output_path, f"parte_{part}")
        create_dir_if_not_exists(current_part_path)

        output_path = os.path.join(ce_path, "rotuladas_cortadas")
        create_dir_if_not_exists(output_path)

        for capo in capos:

            input_path = os.path.join(ce_path, f"rotuladas/{capo}")
            print(input_path)

            try:
                paths = [f for f in os.listdir(input_path)]
            except FileNotFoundError:
                print(f'(Aviso): No such file or directory: {input_path}')
                continue

            images_paths = [os.path.join(input_path, i)
                            for i in paths
                            if i.endswith(('.JPG', '.jpg', '.jpeg', '.JPEG', '.png',))]

            for image_path in \
                    progressBar(images_paths, prefix='Progress:', suffix='Complete', length=50, fill='#'):

                if count >= 50:
                    count = 0
                    part += 1
                    current_part_path = os.path.join(
                        output_path, f"parte_{part}")
                    create_dir_if_not_exists(current_part_path)

                image = Image.open(image_path)
                hood_approximate_height = image.size[1] - int(capo)

                if args.width > image.size[0] or args.height > image.size[1]:
                    log('(Aviso): A largura e/ou largura solicitada(s)'
                        f' excedem o tamanho da imagem {image_path}')
                    continue

                output_image_path = os.path.join(
                    current_part_path, os.path.basename(image_path))
                output_txt_path = os.path.join(
                    current_part_path, get_txt_name(os.path.basename(image_path)))

                cropped_image_rectangle = get_cropped_image_rectangle(
                    image.size, hood_approximate_height, args.width, args.height)

                input_txt_path = get_txt_path(image_path)
                txt_saved = generate_txt(input_txt_path, output_txt_path,
                                         cropped_image_rectangle, image.size)

                if txt_saved:
                    cut(cropped_image_rectangle, image, output_image_path)
                    total_saved += 1
                    count += 1

            print(f'Saved {total_saved} of {len(images_paths)} images')
            print()
