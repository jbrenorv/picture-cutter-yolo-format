from PIL import Image
from shapely.geometry import Polygon
import pandas as pd
import argparse
import os


def get_txt_name(image_name):
    '''
    Retorna o nome do .txt de uma dada imagem
    '''

    split = image_name.split('.')
    split[-1] = 'txt'
    return '.'.join(split)


def get_txt_path(image_path, input_path):
    '''
    Retorna o caminho original para o .txt correspondente uma dada imagem
    '''

    image_name = os.path.basename(image_path)
    txt_name = get_txt_name(image_name)
    return os.path.join(input_path, txt_name)


def get_cropped_image_and_txt_path(image_path, input_path, output_path, replace):
    '''
    Retorna o caminho onde a imagem cortada será salva
    '''

    image_name = os.path.basename(image_path)
    txt_name = get_txt_name(image_name)

    if output_path:
        return (os.path.join(output_path, image_name), os.path.join(output_path, txt_name),)

    if replace:
        return (os.path.join(input_path, image_name), os.path.join(input_path, txt_name),)

    split_image_name = image_name.split('.')
    split_txt_name = txt_name.split('.')

    return (
        os.path.join(input_path,
                     '.'.join(split_image_name[:-1]) + '_cropped.' + split_image_name[-1]),
        os.path.join(input_path,
                     '.'.join(split_txt_name[:-1]) + '_cropped.' + split_txt_name[-1]),)


def cut(left_x, top_y, right_x, bottom_y, input_path, output_path=None, replace=False):
    '''
    Corta imagens

    Parameters
    ----------
        - 'left_x' : Coordenada x da esquerda.
        - 'top_y' : Coordenada y de cima.
        - 'right_x' : Coordenada x da direita.
        - 'bottom_y' : Coordenada y de baixo.
        - 'input_path' : Caminho para as imagens
        - 'output_path' : (Opcional) O caminho para as imagens cortadas
        - 'replace' : Se as imagens devem ser substituidas. Usado apenas se output_path não é definido
    '''

    paths = [os.path.join(input_path, f)
             for f in os.listdir(input_path)]

    images_paths = [i for i in paths if i.endswith((
        '.JPG', '.jpg', '.jpeg', '.JPEG',))]

    if len(images_paths) != \
            len([t for t in paths if t.endswith('.txt')]):
        print("Quantidade de TXTs é diferente da quantidade de imagens.")
        return

    for image_path in images_paths:
        image = Image.open(image_path)

        width, height = image.size

        _x1 = max(0, min(left_x, width))
        _y1 = max(0, min(top_y, height))
        _x2 = max(0, min(right_x, width))
        _y2 = max(0, min(bottom_y, height))

        cropped_image_width = _x2 - _x1
        cropped_image_height = _y2 - _y1

        cropped_image = image.crop((_x1, _y1, _x2, _y2,))
        cropped_image_path, new_txt_path = get_cropped_image_and_txt_path(
            image_path, input_path, output_path, replace)

        txt_path = get_txt_path(image_path, input_path)
        labels = pd.read_csv(txt_path, sep=' ', names=[
            'class', 'x1', 'y1', 'w', 'h'])

        # we need to rescale coordinates from 0-1 to real image height and width
        labels[['x1', 'w']] = labels[['x1', 'w']] * width
        labels[['y1', 'h']] = labels[['y1', 'h']] * height

        boxes = []

        # convert bounding boxes to shapely polygons.
        for row in labels.iterrows():
            x1 = row[1]['x1'] - row[1]['w']/2
            y1 = row[1]['y1'] - row[1]['h']/2
            x2 = row[1]['x1'] + row[1]['w']/2
            y2 = row[1]['y1'] + row[1]['h']/2

            boxes.append((int(row[1]['class']), Polygon(
                [(x1, y1), (x2, y1), (x2, y2), (x1, y2)])))

        cropped_image_pol = Polygon(
            [(_x1, _y1), (_x2, _y1), (_x2, _y2), (_x1, _y2)])
        txt_rows = []

        for box in boxes:
            if cropped_image_pol.intersects(box[1]):
                inter = cropped_image_pol.intersection(box[1])
                new_box = inter.envelope

                # get central point for the new bounding box
                centre = new_box.centroid

                # get coordinates of polygon vertices
                x, y = new_box.exterior.coords.xy

                # get bounding box width and height normalized to slice size
                new_width = (max(x) - min(x)) / cropped_image_width
                new_height = (max(y) - min(y)) / cropped_image_height

                # we have to normalize central x and invert y for yolo format
                new_x = (centre.coords.xy[0][0] - left_x) / cropped_image_width
                new_y = (centre.coords.xy[1][0] - top_y) / cropped_image_height

                txt_rows.append(
                    [box[0], new_x, new_y, new_width, new_height])

        if len(txt_rows) > 0:
            slice_df = pd.DataFrame(txt_rows, columns=[
                'class', 'x1', 'y1', 'w', 'h'])
            slice_df.to_csv(new_txt_path, sep=' ',
                            index=False, header=False, float_format='%.6f')
            cropped_image.save(cropped_image_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-left_x", type=int, default=410,
                        help="Coordenada x da esquerda. Dafault: 410")
    parser.add_argument("-right_x", type=int, default=3580,
                        help="Coordenada x da direita. Dafault: 3580")
    parser.add_argument("-top_y", type=int, default=1080,
                        help="Coordenada y de cima. Dafault: 1080")
    parser.add_argument("-bottom_y", type=int, default=1950,
                        help="Coordenada y de baixo. Dafault: 1950")
    parser.add_argument("-input_path", default="./data/input_images/",
                        help="Caminho para as imagens")
    parser.add_argument("-output_path", default=None,
                        help="(Opcional) O caminho para as imagens cortadas")
    parser.add_argument("-replace", type=int, default=0,
                        help="Se definido como 1 (ou qualquer inteiro diferente de 0) e output_path nao for definido, as imagens serao substituidas. Dafault: 0")

    args = parser.parse_args()

    if args.output_path:
        if not os.path.exists(args.output_path):
            os.makedirs(args.output_path)

    cut(args.left_x, args.top_y, args.right_x, args.bottom_y,
        args.input_path, args.output_path, args.replace != 0)
