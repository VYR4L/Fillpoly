import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QMenu, QColorDialog
from PyQt6.QtGui import QCursor
import sys


drawing = False  # Se o usuário está desenhando um polígono
polygon_points = []  # Lista de pontos do polígono atual
polygons = []  # Lista de polígonos desenhados (pontos e cor)
current_polygon = None  # Polígono atual
fill_edges = True  # Se devemos desenhar as arestas do polígono
selected_polygon_index = None  # Índice do polígono selecionado

initial_color = (171, 0, 111)  # Cor inicial (roxo) BGR 
edge_color = (0, 255, 255)  # Amarelo


def draw_polygon(img, points, color, edges=True):
    '''
    Função para desenhar e preencher um polígono usando um algoritmo de varredura.

    param img: Imagem onde o polígono será desenhado
    param points: Lista de pontos do polígono
    param color: Cor do polígono
    param edges: Se devemos desenhar as arestas do polígono
    '''
    # Se temos pelo menos 3 pontos para formar um polígono
    if len(points) > 2:
        # Preencher o polígono usando o algoritmo de varredura
        fill_polygon(img, points, color)
        # Se edges for True, desenha as arestas do polígono
        if edges:
            cv2.polylines(img, [np.array(points, np.int32)], isClosed=True, color=edge_color, thickness=2)


def fill_polygon(img, points, color):
    '''
    Preenche um polígono com a cor especificada usando o algoritmo de varredura.

    param img: Imagem onde o polígono será preenchido
    param points: Lista de pontos do polígono
    param color: Cor usada para preencher o polígono (BGR)
    '''
    # Encontrar os valores mínimo e máximo de y (altura) para a varredura
    points = np.array(points, np.int32)
    min_y = np.min(points[:, 1])
    max_y = np.max(points[:, 1])

    # Varre cada linha entre min_y e max_y
    for y in range(min_y, max_y + 1):
        # Encontra todas as interseções entre a linha y e as arestas do polígono
        intersec_x = []

        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]  # Pega o próximo ponto, formando a aresta

            # Verifica se a linha y intersecta a aresta (p1, p2)
            if (p1[1] <= y < p2[1]) or (p2[1] <= y < p1[1]):  # Apenas se há intersecção em y
                # Calcula o ponto de interseção em x usando interpolação linear
                x = int(p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1]))
                intersec_x.append(x)

        # Ordena os pontos de interseção em x
        intersec_x.sort()

        # Preenche os segmentos da linha
        for i in range(0, len(intersec_x), 2):
            if i + 1 < len(intersec_x):  # Para evitar pares incompletos
                cv2.line(img, (intersec_x[i], y), (intersec_x[i + 1], y), color)


def mouse_callback(event, x, y, flags, param):
    '''
    Função de callback para eventos do mouse.

    param event: Evento do mouse
    param x: Coordenada x do cursor
    param y: Coordenada y do cursor
    param flags: Flags do OpenCV
    param param: Parâmetro extra
    '''
    global drawing, polygon_points, current_polygon, selected_polygon_index

    if event == cv2.EVENT_LBUTTONDOWN:
        if not drawing:
            # Inicia um novo polígono
            polygon_points = [(x, y)]
            drawing = True
        else:
            # Adiciona pontos ao polígono
            polygon_points.append((x, y))

    elif event == cv2.EVENT_RBUTTONDOWN:
        # Seleciona um polígono para alteração de cor ou exclusão
        for i, (points, color) in enumerate(polygons):
            if cv2.pointPolygonTest(np.array(points), (x, y), False) >= 0:
                selected_polygon_index = i
                show_options_menu(x, y)


def show_options_menu(x, y):
    '''
    Função para exibir um menu de contexto com opções para o polígono selecionado.

    param x: Coordenada x do cursor
    param y: Coordenada y do cursor
    '''
    app = QApplication.instance()  # Reutiliza a instância existente do QApplication
    if app is None:
        app = QApplication(sys.argv)

    menu = QMenu()
    change_color_action = menu.addAction("Alterar cor")
    delete_polygon_action = menu.addAction("Excluir polígono")

    action = menu.exec(QCursor.pos())  # Exibe o menu de contexto na posição do cursor

    if action == change_color_action:
        change_polygon_color(selected_polygon_index)
    elif action == delete_polygon_action:
        delete_polygon(selected_polygon_index)


def change_polygon_color(polygon_index):
    '''
    Função para alterar a cor de um polígono.

    param polygon_index: Índice do polígono na lista de polígonos
    '''
    color = QColorDialog.getColor()  # Abre um seletor de cor
    if color.isValid():
        new_color = (color.blue(), color.green(), color.red())  # Convertendo para BGR
        polygons[polygon_index] = (polygons[polygon_index][0], new_color)


def delete_polygon(polygon_index):
    '''
    Função para excluir um polígono da lista.

    param polygon_index: Índice do polígono na lista de polígonos
    '''
    global polygons
    polygons.pop(polygon_index)


# Configurações da janela
cv2.namedWindow("Polygons")
cv2.setMouseCallback("Polygons", mouse_callback)


# Janela principal do programa
def main():
    global drawing, polygon_points, polygons, current_polygon, fill_edges

    # Dimensões da tela
    width, height = 800, 600
    img = np.ones((height, width, 3), dtype=np.uint8) * 255

    while True:
        temp_img = img.copy()

        # Desenha o polígono atual enquanto o usuário clica os pontos
        if drawing and len(polygon_points) > 0:
            draw_polygon(temp_img, polygon_points, initial_color, edges=fill_edges)

        # Desenha todos os polígonos confirmados
        for points, color in polygons:
            draw_polygon(temp_img, points, color, edges=fill_edges)

        # Exibe a imagem
        cv2.imshow("Polygons", temp_img)

        # Captura as teclas pressionadas
        key = cv2.waitKey(1) & 0xFF
        if key == 13 or key == 32:  # Enter ou espaço: finaliza o polígono atual
            if len(polygon_points) > 2:
                polygons.append((polygon_points.copy(), initial_color))
            drawing = False
            polygon_points = []

        elif key == 27:  # Esc: fecha o programa
            break

        elif key == ord('a'):  # Alterna entre desenhar ou não as arestas
            fill_edges = not fill_edges

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
