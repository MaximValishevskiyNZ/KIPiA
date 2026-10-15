#!/usr/bin/env python3
"""Generate editable SVG artwork using the repository's design tokens."""
from html import escape
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
C = json.loads((ROOT / 'Оформление/tokens.json').read_text())['colors']
MEDIA = ROOT / 'Тех карты/Уровень/Endress+Hauser/Prosonic/media'


def text(x, y, value, size=22, color='ink', weight='normal', anchor='start'):
    return f'<text x="{x}" y="{y}" font-family="DejaVu Sans, Arial, sans-serif" font-size="{size}" fill="{C.get(color, color)}" font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>'


def box(x, y, w, h, fill='surface', stroke='line', radius=14):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{C.get(fill, fill)}" stroke="{C.get(stroke, stroke)}" stroke-width="2"/>'


def line(x1, y1, x2, y2, color='signal', dash=False, arrow=False):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{C.get(color,color)}" stroke-width="3"' + (' stroke-dasharray="9 7"' if dash else '') + (' marker-end="url(#arrow)"' if arrow else '') + '/>'


def path(points, color='signal'):
    return f'<polyline points="{points}" fill="none" stroke="{C[color]}" stroke-width="3" stroke-linejoin="round"/>'


def heading(title, subtitle):
    return text(46, 58, title, 30, weight='bold') + text(46, 96, subtitle, 20, 'muted')


def save(target, title, desc, body, height=620, dark=False):
    target.parent.mkdir(parents=True, exist_ok=True)
    bg = C['ink'] if dark else C['canvas']
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>
<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L7,3 L0,6" fill="none" stroke="{C['signal']}" stroke-width="1.4"/></marker></defs>
<rect width="1200" height="{height}" rx="18" fill="{bg}"/>
<g font-family="DejaVu Sans, Arial, sans-serif">{body}</g></svg>'''
    target.write_text(svg + '\n')


def loop(filename, model, limit, source):
    b = heading(f'{model} · двухпроводная петля', 'Отдельное питание + пассивный токовый вход; обычная зона, без барьера')
    b += box(70, 165, 245, 150) + text(96, 204, 'Источник DC', 24, weight='bold')
    b += text(96, 245, 'U по расчёту петли', 19, 'muted')
    b += text(265, 297, '+', 25, weight='bold') + text(95, 297, '−', 25, weight='bold')
    b += box(450, 165, 300, 150) + text(476, 204, model, 24, weight='bold')
    b += text(476, 245, 'Питание и сигнал вместе', 18, 'muted')
    b += text(480, 297, '2 · L+', 22, weight='bold') + text(650, 297, '1 · L−', 22, weight='bold')
    b += box(875, 165, 255, 150) + text(899, 204, 'Вход ПЛК', 24, weight='bold')
    b += text(899, 245, 'Пассивный, 4–20 мА', 18, 'muted')
    b += text(899, 297, 'AI+', 22, weight='bold') + text(1048, 297, 'AI−', 22, weight='bold')
    b += path('276,315 276,358 505,358 505,315')
    b += path('692,315 692,358 920,358 920,315')
    b += path('1070,315 1070,410 108,410 108,315')
    b += text(370, 346, 'I →', 22, 'signal', weight='bold')
    b += text(55, 472, limit, 22, weight='bold')
    b += text(55, 512, 'Земля / уравнивание потенциалов — отдельное соединение по инструкции.', 19, 'muted')
    b += text(55, 551, 'Активный вход ПЛК требует своей схемы; второй источник вслепую не добавлять.', 19, 'attention')
    b += text(55, 592, source, 18, 'muted')
    save(MEDIA / filename, model + ': токовая петля', 'Плюс источника на 2 L+, 1 L− на AI+, AI− на минус источника. Земля не является сигнальным минусом.', b)


def main():
    b = text(60, 66, 'ПРАКТИЧЕСКАЯ БАЗА ЗНАНИЙ', 18, '#B3DFDC', weight='bold')
    b += text(55, 168, 'КИПиА', 88, '#FFFFFF', weight='bold')
    b += text(60, 228, 'Приборы, которые понятны.', 30, '#FFFFFF')
    b += text(60, 283, 'Техкарты · схемы · диагностика', 23, '#D2DFEB')
    b += text(60, 323, 'На основе официальных документов', 20, '#D2DFEB')
    b += box(860, 75, 230, 275, '#1C3955', '#48617A')
    for yy in range(110, 315, 35):
        b += line(885, yy, 912, yy, '#A3B8CA')
    b += box(942, 108, 95, 207, '#28465F', '#48617A', 8)
    b += box(949, 191, 81, 117, '#36B6AC', '#36B6AC', 6)
    b += text(1054, 177, 'L', 24, '#FFFFFF', weight='bold')
    b += line(836, 191, 1108, 191, '#F0B56C', dash=True)
    save(ROOT / '.github/assets/cover.svg', 'КИПиА', 'Практическая база знаний: техкарты, схемы и диагностика по официальным документам.', b, height=400, dark=True)

    b = heading('Геометрия измерения уровня', 'Непосредственное измерение поверхности; схема без масштаба')
    b += box(100, 180, 520, 425, stroke='ink', radius=4)
    b += box(295, 125, 125, 55, fill='ink', stroke='ink', radius=8)
    b += box(103, 183, 514, 65, '#FAE8D5', '#FAE8D5', 0)
    b += text(125, 224, 'BD · ближняя зона', 22, 'attention')
    b += box(103, 410, 514, 192, '#CDEAE7', '#CDEAE7', 0)
    b += line(100, 300, 620, 300, 'muted', dash=True) + text(125, 287, '100% рабочего диапазона', 20)
    b += line(100, 410, 620, 410) + text(125, 449, 'Поверхность продукта', 22, 'signal')
    b += line(100, 580, 620, 580, 'ink', dash=True) + text(125, 568, '0% · выбранный ноль', 20)
    b += line(357, 180, 357, 410, dash=True)
    for x, top, bottom, name in [(715,180,580,'E'), (815,180,410,'D'), (915,300,580,'F'), (1015,410,580,'L')]:
        b += line(x, top, x, bottom, arrow=True)
        b += line(x-13, top, x+13, top, 'ink')
        b += text(x+15, (top+bottom)/2, name, 28, weight='bold')
    b += text(690, 145, 'Отсчёт от мембраны', 20, 'muted')
    b += text(680, 638, 'L = E − D', 30, 'signal', weight='bold')
    b += text(45, 683, 'T1, с.31; M1, с.41,45; S1, с.51. Для отражателя поплавка нужна привязка к уровню.', 18, 'muted')
    save(MEDIA / 'геометрия.svg', 'Геометрия E, F, D, L и BD', 'E от мембраны до нуля. D до продукта. F высота рабочего диапазона. L фактический уровень. Верхняя точка не входит в BD.', b, height=710)

    loop('петля-fmu30.svg', 'FMU30', 'На клеммах FMU30: 14–35 В DC. Предохранитель: T 0,5 А по T1.', 'Источник: T1, с.16–18. Номера клемм сверены с заводской схемой.')
    loop('петля-prosonic-m.svg', 'Prosonic M HART', 'Напряжение на приборе зависит от исполнения и тока: таблица M1, с.29.', 'Источник: M1, с.29. Для HART ≥250 Ом в цепи; проверить суммарную нагрузку.')

    b = heading('Prosonic M HART · четыре провода', 'Активный токовый выход подключается к пассивному входу ПЛК')
    b += box(55, 180, 275, 190) + text(80, 218, 'Питание по шильдику', 22, weight='bold')
    b += text(80, 263, '10,5–32 В DC', 23) + text(80, 302, 'ИЛИ 90–253 В AC', 23)
    b += text(80, 341, 'Разные исполнения', 19, 'attention')
    b += box(455, 155, 300, 300) + text(479, 196, 'Prosonic M HART', 24, weight='bold')
    b += text(479, 247, '1 · L1/L+', 23) + text(479, 294, '2 · N/L−', 23)
    b += text(585, 365, '5 · I+', 23, 'signal', weight='bold') + text(585, 412, '6 · I−', 23, 'signal', weight='bold')
    b += box(880, 290, 270, 165) + text(902, 330, 'Вход ПЛК', 24, weight='bold')
    b += text(902, 366, 'AI+ · пассивный', 20) + text(902, 413, 'AI−', 20)
    b += path('330,239 420,239 420,239 455,239') + path('330,286 455,286')
    b += line(755, 357, 880, 357, arrow=True) + line(880, 404, 755, 404)
    b += text(55, 520, 'Нагрузка активного выхода: максимум 600 Ом. Питание на выход не подавать.', 22, weight='bold')
    b += text(55, 563, 'Земля и защита цепи питания — по инструкции конкретного исполнения.', 20, 'muted')
    b += text(55, 601, 'Источник: M1, с.29–30. Схема только для 4-wire HART, не PA/FF.', 18, 'muted')
    save(MEDIA / 'четыре-провода-prosonic-m.svg', 'Prosonic M HART: раздельное питание и выход', 'Клеммы 1 и 2 питание, 5 и 6 активный выход. Пассивный вход ПЛК. Питание выбирают по исполнению.', b)

    b = heading('Prosonic S · FDU + FMU90', 'Датчик FDU не подключается напрямую к обычному входу 4–20 мА')
    b += box(55, 205, 250, 190) + text(80, 246, 'Датчик FDU', 27, weight='bold')
    for y, s in [(293,'YE · жёлтый'),(333,'BK · чёрный / экран'),(373,'RD · красный')]: b += text(80, y, s, 18)
    b += box(430, 155, 320, 325) + text(456, 198, 'FMU90 HART', 27, weight='bold')
    b += text(456, 242, 'Вход датчика 1:', 20, 'muted')
    for y, s in [(293,'9 · YE'),(333,'10 · BK'),(373,'11 · RD')]: b += text(456, y, s, 22)
    b += text(456, 433, 'Выход 1: клеммы 4 / 5', 20, 'signal', weight='bold')
    for y in [286,326,366]: b += line(305,y,430,y)
    b += box(880, 330, 260, 135) + text(906, 371, 'Система управления', 19, weight='bold')
    b += text(906, 415, 'Вход 0/4–20 мА', 22)
    b += line(750,425,880,425,arrow=True)
    b += text(800, 297, 'Сигнал выхода', 18, 'muted')
    b += text(55, 526, 'Питание FMU90 отдельно: 1 / 2 / 3 по AC- или DC-исполнению.', 22, weight='bold')
    b += text(55, 563, 'GNYE, если есть, не объединять с BK. Наличие второго входа — по комплектации.', 19, 'attention')
    b += text(55, 601, 'Источник: S1, с.24–29. Полярность выхода и земля — по маркировке и полной схеме.', 18, 'muted')
    save(MEDIA / 'система-fmu90.svg', 'FDU и отдельный FMU90', 'Три проводника FDU на 9 YE, 10 BK, 11 RD. Питание FMU90 отдельно. Аналоговый выход 4/5 идёт в систему управления.', b)

    b = heading('Поплавок и отражатель · возможная компоновка', 'Рабочая гипотеза по описанию участка; не заводской чертёж вашего узла')
    b += box(70, 365, 640, 270, stroke='ink', radius=4)
    b += box(73, 500, 634, 132, '#CDEAE7', '#CDEAE7', 0)
    b += box(73, 410, 634, 90, '#F6E9CF', '#F6E9CF', 0)
    b += text(92, 449, 'Пенный слой', 20, 'attention') + text(92, 588, 'Пульпа', 22, 'signal')
    b += box(300, 150, 140, 55, fill='ink', stroke='ink', radius=8)
    b += text(285, 132, 'Prosonic / FDU', 23, weight='bold')
    b += box(292, 302, 156, 16, fill='signal', stroke='signal', radius=2)
    b += line(370, 318, 370, 506, 'ink')
    b += '<ellipse cx="370" cy="508" rx="68" ry="46" fill="#FFFFFF" stroke="#14283F" stroke-width="3"/>'
    b += text(325, 516, 'Поплавок', 18)
    b += line(370, 205, 370, 300, dash=True) + line(550,205,550,302,arrow=True)
    b += text(566, 264, 'D до цели', 22, 'signal', weight='bold')
    b += text(466, 343, 'Отражатель', 20) + line(448,310,560,310,'muted')
    b += text(748, 199, 'Проверить на месте:', 24, weight='bold')
    for y,s in [(245,'1. Что служит целью'),(290,'2. Свободный ход'),(335,'3. Связь с уровнем'),(380,'4. Эхо от нужной цели'),(425,'5. Запас до BD')]: b += text(748,y,s,21)
    b += text(748, 495, 'Размеры, плавучесть', 20, 'muted') + text(748, 527, 'и направляющие —', 20, 'muted') + text(748,559,'по паспорту узла.',20,'muted')
    b += text(45, 681, 'Инженерная иллюстрация. A1 подтверждает FDU91 для флотации, но не эту механику.', 18, 'muted')
    save(MEDIA / 'поплавок-флотация.svg', 'Возможная схема Prosonic с поплавком', 'Ультразвуковой датчик над отражателем на штоке поплавка. Положение и устройство поплавка условны; необходимо проверить фактический узел.', b, height=710)

    b = heading('{Устройство} · {название схемы}', 'Исполнение: {модель / интерфейс / питание}; статус: {подтверждено / условно}')
    for x,name in [(65,'Вход / источник'),(465,'Устройство'),(865,'Выход / система')]:
        b += box(x,220,270,170) + text(x+22,270,name,21,weight='bold')
        b += text(x+22,320,'{клеммы и назначение}',18)
    b += line(335,305,465,305,arrow=True) + line(735,305,865,305,arrow=True)
    b += text(55,490,'Ограничения: {указать границы применимости и условные элементы}',20,'attention')
    b += text(55,560,'Источник: {документ, редакция, напечатанная страница / раздел}',19,'muted')
    save(ROOT/'Оформление/схема-шаблон.svg','Шаблон инженерной схемы','Заменить устройства, номера клемм, направление сигнала, применимость и источник.',b)
    print('SVG: cover + 6 diagrams + template generated')


if __name__ == '__main__':
    main()
