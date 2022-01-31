from PIL import Image
from shapely.geometry import Polygon
import pandas as pd
import argparse
import shutil
import os

from utils import Rectangle, find_highway_region


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


def get_cropped_image_and_txt_path(image_path, output_path, suffix_text):
    '''
    Retorna o caminho onde a imagem cortada e o txt serao salva
    '''

    image_name = os.path.basename(image_path)
    txt_name = get_txt_name(image_name)
    split_image_name = image_name.split('.')
    split_txt_name = txt_name.split('.')
    cropped_image_name = '.'.join(
        split_image_name[:-1]) + suffix_text + '.' + split_image_name[-1]
    cropped_txt_name = '.'.join(
        split_txt_name[:-1]) + suffix_text + '.' + split_txt_name[-1]

    return (os.path.join(output_path, cropped_image_name),
            os.path.join(output_path, cropped_txt_name),)


def cropped_image_rectangle_from_highway_region(highway_region: Rectangle, width: int, height: int,
                                                original_image_size):
    '''
    Define a regiao de corte, dada a regiao da rodovia
    '''

    hood_approximate_height = 240
    x_min = max(0, highway_region.centre_x() - (width // 2))
    x_max = x_min + width
    y_min = \
        highway_region.y_min \
        if highway_region.height() >= height \
        else highway_region.y_max - height
    y_min = max(0, y_min)
    y_max = y_min + height

    # se o corte estiver muito na parte de cima, esta errado, pois vai pegar so o ceu
    # if y_max < (original_image_size[1] - hood_approximate_height):
    #     y_max = original_image_size[1] - hood_approximate_height
    #     y_min = y_max - height
    if ((original_image_size[1] - hood_approximate_height) - y_max) > \
            2 * hood_approximate_height:
        y_max = original_image_size[1] - int(hood_approximate_height * 1.5)
        y_min = y_max - height

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

    print(f"(Aviso): Sem conteudo para {input_txt_path}")

    return False


def create_dir_if_not_exists(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-width", type=int, default=2100,
                        help="A largura das novas imagens. Dafault: 2100")
    parser.add_argument("-height", type=int, default=800,
                        help="A altura das novas imagens. Dafault: 800")
    parser.add_argument("-input_path", required=True,
                        help="Caminho para as imagens")
    parser.add_argument("-output_path", default=None,
                        help="(Opcional) O caminho para as imagens cortadas")
    parser.add_argument("-replace", type=int, default=0,
                        help="Se definido como 1 (ou qualquer inteiro diferente de 0) e output_path nao for definido, as imagens serao substituidas. Dafault: 0")

    args = parser.parse_args()

    paths = [f for f in os.listdir(args.input_path)]
    suffix_output_files_text = ''
    output_path = args.input_path
    logs_path_created = False
    logs_path = "./logs"  # + os.path.basename(args.input_path)

    if args.output_path and args.output_path != args.input_path:
        output_path = args.output_path

        create_dir_if_not_exists(args.output_path)

        classes_file_name = "classes.txt"
        if classes_file_name in paths:
            paths.remove(classes_file_name)
            shutil.copyfile(os.path.join(args.input_path, classes_file_name),
                            os.path.join(args.output_path, classes_file_name))
    elif args.replace != 0:
        suffix_output_files_text = '_cropped'

    images_paths = [os.path.join(args.input_path, i)
                    for i in paths
                    if i.endswith(('.JPG', '.jpg', '.jpeg', '.JPEG', '.png',))]
    cnt = 1
    total = len(images_paths)

    for image_path in images_paths:

        print(f'{cnt}/{total}')
        cnt += 1

        highway_region = find_highway_region(image_path)

        if highway_region:

            image = Image.open(image_path)
            if args.width > image.size[0] or args.height > image.size[1]:
                print('(Aviso): A largura e/ou largura solicitada(s)'
                      f' excedem o tamanho da imagem {image_path}')
                continue

            output_image_path, output_txt_path = get_cropped_image_and_txt_path(
                image_path, output_path, suffix_output_files_text)

            cropped_image_rectangle = cropped_image_rectangle_from_highway_region(
                highway_region, args.width, args.height, image.size)

            input_txt_path = get_txt_path(image_path)
            txt_saved = generate_txt(input_txt_path, output_txt_path,
                                     cropped_image_rectangle, image.size)

            if txt_saved:
                cut(cropped_image_rectangle, image, output_image_path)
            else:
                if not logs_path_created:
                    create_dir_if_not_exists(logs_path)
                    logs_path_created = True

                cut(cropped_image_rectangle, image,
                    os.path.join(logs_path, os.path.basename(output_image_path)))

        else:
            print(f'(Aviso): Rodovia não identificada em {image_path}')
