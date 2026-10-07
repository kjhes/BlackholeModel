# 블랙홀 복리 프로그램
# 달마다 넣는 돈이 복리로 변한 양을, 시간이 지날수록 커지는 블랙홀의 나선으로 보여 준다.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, TextBox

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

GAIN_COLOR = "#ffb000"  # 이익: 주황
LOSS_COLOR = "#ff3b3b"  # 손실: 빨강
TURN_YEARS = 5          # 나선이 한 바퀴 도는 데 걸리는 햇수
COLUMNS = 4             # 펼친 화면에서 한 줄에 그리는 블랙홀 수
HELP = "값을 넣고 [실행]을 누르세요. 수익률에는 음수도 넣을 수 있습니다. 왼쪽 블랙홀을 누르면 여러 모형이 펼쳐집니다."


# ---------- 모형별 계산 함수 ----------
# 모든 함수는 달마다의 금액 리스트를 돌려준다. [0개월째, 1개월째, ..., 마지막 달]

def paid_in(monthly, years):
    """넣은 돈: 이자 없이 그냥 쌓기만 했을 때의 금액."""
    amounts = [0]
    for month in range(years * 12):
        amounts.append(amounts[-1] + monthly)
    return amounts


def compound(monthly, rate, years, period):
    """복리의 반복 구조. period개월마다 그동안 쌓인 이자를 금액에 합친다.

    합쳐진 금액이 다음 계산에 다시 들어가므로 이자에도 이자가 붙는다.
    """
    amount = 0
    waiting = 0  # 붙었지만 아직 금액에 합쳐지지 않은 이자
    amounts = [amount]
    for month in range(1, years * 12 + 1):
        amount = amount + monthly
        waiting = waiting + amount * rate / 12
        if month % period == 0:
            amount = amount + waiting
            waiting = 0
        amounts.append(amount)
    return amounts


def yearly_compound(monthly, rate, years):
    """연 복리: 1년에 한 번 이자를 합친다."""
    return compound(monthly, rate, years, 12)


def monthly_compound(monthly, rate, years):
    """월 복리: 달마다 이자를 합친다."""
    return compound(monthly, rate, years, 1)


def actual_compound(monthly, rates):
    """실제 수익률: 해마다 그 해의 실제 수익률로 연 복리 계산을 한다.

    수익률이 음수인 해에는 쌓인 금액이 그만큼 줄어든다.
    """
    amount = 0
    waiting = 0
    amounts = [amount]
    for rate in rates:
        for month in range(1, 13):
            amount = amount + monthly
            waiting = waiting + amount * rate / 12
            if month == 12:
                amount = amount + waiting
                waiting = 0
            amounts.append(amount)
    return amounts


def reflect_inflation(amounts, inflation):
    """물가 반영: 그동안 물가가 오른 만큼 금액을 나눈다."""
    real = []
    for month in range(len(amounts)):
        real.append(amounts[month] / (1 + inflation) ** (month / 12))
    return real


# ---------- 실제 자료에서 가져온 모형 ----------
# (이름, 연 수익률 %, 복리 계산 함수, 물가 상승률 % 또는 None)
#
# 수익률 출처 (2026-10 확인)
# - 은행 정기예금 3.21%: 한국은행, 2026년 8월 예금은행 신규취급액 기준 저축성수신금리
# - 한국 물가 2.0%: 한국은행 물가안정목표
# - 코스피 7.5%: 2005년부터 20년, 배당 포함 추정 연평균
# - S&P 500 10.4%: 1957~2025년, 배당 재투자 연평균
# - 미국 물가 3.7%: S&P 500의 같은 기간 물가 반영 수익률 6.5%에서 거꾸로 계산한 값
# - 나스닥 100 14.25%: 1985~2024년 연평균
# - 버크셔 해서웨이 19.9%: 1965~2024년, 워런 버핏 주주 서한
MODELS = [
    ("은행 정기예금", 3.21, monthly_compound, None),
    ("은행 정기예금\n물가 반영", 3.21, monthly_compound, 2.0),
    ("코스피", 7.5, yearly_compound, None),
    ("나스닥 100", 14.25, yearly_compound, None),
    ("버크셔 해서웨이", 19.9, yearly_compound, None),
    ("S&P 500", 10.4, yearly_compound, None),
    ("S&P 500\n물가 반영", 10.4, yearly_compound, 3.7),
]

# S&P 500의 해마다 실제 수익률 %, 배당 포함. 1966년부터 2025년까지 차례대로.
# 출처: 뉴욕대 스턴 경영대학원 다모다란 교수 자료 (2026-10 확인)
SP500_FIRST_YEAR = 1966
SP500_ACTUAL = [
    -9.97, 23.80, 10.81, -8.24,                                             # 1966~1969
    3.56, 14.22, 18.76, -14.31, -25.90, 37.00, 23.83, -6.98, 6.51, 18.52,   # 1970~1979
    31.74, -4.70, 20.42, 22.34, 6.15, 31.24, 18.49, 5.81, 16.54, 31.48,     # 1980~1989
    -3.06, 30.23, 7.49, 9.97, 1.33, 37.20, 22.68, 33.10, 28.34, 20.89,      # 1990~1999
    -9.03, -11.85, -21.97, 28.36, 10.74, 4.83, 15.61, 5.48, -36.55, 25.94,  # 2000~2009
    14.82, 2.10, 15.89, 32.15, 13.52, 1.38, 11.77, 21.61, -4.23, 31.21,     # 2010~2019
    18.02, 28.47, -18.04, 26.06, 24.88, 17.78,                              # 2020~2025
]


def calculate(monthly, years, my_rate):
    """모형마다 달마다의 금액을 계산한다.

    돌려주는 값: 넣은 돈 리스트, 일정한 수익률 모형들, 실제 데이터 모형
    모형 하나는 (설명, 금액 리스트, 해마다의 실제 수익률 또는 None)이다.
    """
    paid = paid_in(monthly, years)

    # 일정한 수익률 모형: 내가 입력한 수익률이 맨 앞, 그 뒤로 실제 자료에서 가져온 모형들
    results = {}
    amounts = yearly_compound(monthly, my_rate / 100, years)
    results["입력한 수익률"] = (f"연 {my_rate:g}%, 연 복리", amounts, None)
    for name, rate, function, inflation in MODELS:
        amounts = function(monthly, rate / 100, years)
        if function == monthly_compound:
            note = f"연 {rate:g}%, 월 복리"
        else:
            note = f"연 {rate:g}%, 연 복리"
        if inflation is not None:
            amounts = reflect_inflation(amounts, inflation / 100)
            note += f", 물가 {inflation:g}%"
        results[name] = (note, amounts, None)

    # 실제 데이터 모형: 가장 최근 years년 동안의 S&P 500 실제 수익률을 차례대로 쓴다.
    rates = SP500_ACTUAL[-years:]
    first_year = SP500_FIRST_YEAR + len(SP500_ACTUAL) - years
    yearly = [(first_year + index, rate) for index, rate in enumerate(rates)]
    amounts = actual_compound(monthly, [rate / 100 for rate in rates])
    actual = (f"S&P 500, {first_year}~{yearly[-1][0]}년 실제 수익률", amounts, yearly)
    return paid, results, actual


# ---------- 표 출력 ----------

def print_table(paid, results, years):
    """해마다의 금액과, 바로 전 해보다 늘어난 양을 표 두 개로 출력한다."""
    header = f"{'해':>3} | {'넣은 돈':>8} "
    for name in results:
        header += f"| {name.replace(chr(10), ' '):>14} "

    print()
    print("[해마다의 금액]")
    print(header)
    for year in range(years + 1):
        month = year * 12
        line = f"{year:>4} | {paid[month]:>11.0f} "
        for note, amounts, yearly in results.values():
            line += f"| {amounts[month]:>16.0f} "
        print(line)

    print()
    print("[바로 전 해보다 늘어난 양]")
    print(header)
    for year in range(1, years + 1):
        month = year * 12
        line = f"{year:>4} | {paid[month] - paid[month - 12]:>11.0f} "
        for note, amounts, yearly in results.values():
            line += f"| {amounts[month] - amounts[month - 12]:>+16.0f} "
        print(line)


# ---------- 그림 ----------

def draw(fig, paid, results, years, headline, columns):
    """모형마다 블랙홀을 하나씩 그린다.

    나선의 중심에서 끝까지의 거리 = 넣은 돈에서 변한 양의 크기.
    시간이 지날수록 나선이 돌면서 바깥으로 자란다. (5년에 한 바퀴)
    이익이면 주황, 손실이면 빨강.
    처음에는 모든 칸의 눈금이 같아서 크기를 바로 견줄 수 있다.
    set_scale(True)를 부르면 칸마다 제 크기에 맞춰 확대해서 나선의 모양을 볼 수 있다.
    """
    months = years * 12
    names = list(results.keys())
    paid = np.array(paid)
    angle = 2 * np.pi * np.arange(months + 1) / (TURN_YEARS * 12)

    # 모든 모형, 모든 달을 통틀어 가장 큰 변화량에 화면 크기를 맞춘다.
    biggest = 0
    for note, amounts, yearly in results.values():
        biggest = max(biggest, np.abs(np.array(amounts) - paid).max())
    if biggest == 0:
        biggest = 1
    limit = biggest * 1.15

    rows = (len(names) + columns - 1) // columns
    grid = fig.add_gridspec(rows, columns, left=0.03, right=0.97,
                            top=0.85, bottom=0.2, hspace=0.75)
    title = fig.suptitle("", color="white", fontsize=18)

    axes = []
    own_limits = []
    panels = []
    for index, name in enumerate(names):
        note, amounts, yearly = results[name]
        ax = fig.add_subplot(grid[index // columns, index % columns])
        axes.append(ax)
        ax.set_facecolor("black")
        ax.set_xlim(-limit, limit)
        ax.set_ylim(-limit, limit)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"{name.replace(chr(10), ' ')}\n{note}", color="white", fontsize=13)

        change = np.array(amounts) - paid
        radius = np.abs(change)
        if radius.max() == 0:
            own_limits.append(1)
        else:
            own_limits.append(radius.max() * 1.15)

        # 나선 팔 두 개. 팔마다 흐릿한 굵은 선 위에 선명한 가는 선을 겹친다.
        arms = []
        for turn in (0, np.pi):
            x = radius * np.cos(angle + turn)
            y = radius * np.sin(angle + turn)
            glow, = ax.plot([], [], linewidth=5, alpha=0.25)
            line, = ax.plot([], [], linewidth=1.3)
            arms.append((x, y, glow, line))

        horizon = plt.Circle((0, 0), 0, fill=False, linewidth=1, alpha=0.6)
        ax.add_patch(horizon)

        label = ax.text(0.5, -0.03, "", color="white", fontsize=11,
                        ha="center", va="top", transform=ax.transAxes)
        panels.append((amounts, change, yearly, arms, horizon, label))

    def update(month):
        title.set_text(f"{month // 12}년 {month % 12}개월째   {headline}   넣은 돈 {paid[month]:,.0f}")
        for amounts, change, yearly, arms, horizon, label in panels:
            if change[month] >= 0:
                color = GAIN_COLOR
                word = "이익"
            else:
                color = LOSS_COLOR
                word = "손실"
            for x, y, glow, line in arms:
                glow.set_data(x[:month + 1], y[:month + 1])
                line.set_data(x[:month + 1], y[:month + 1])
                glow.set_color(color)
                line.set_color(color)
            horizon.set_radius(abs(change[month]))
            horizon.set_edgecolor(color)
            text = f"금액 {amounts[month]:,.0f}\n{word} {change[month]:+,.0f}"
            if yearly is not None and month > 0:
                year, rate = yearly[(month - 1) // 12]
                text += f"\n{year}년 수익률 {rate:+.2f}%"
            label.set_text(text)
            label.set_color(color)

    def set_scale(zoom):
        for ax, own_limit in zip(axes, own_limits):
            if zoom:
                size = own_limit
            else:
                size = limit
            ax.set_xlim(-size, size)
            ax.set_ylim(-size, size)

    # 기간이 길어도 움직임이 너무 길어지지 않게 건너뛰며 그린다.
    step = max(1, months // 360)
    frames = list(range(0, months, step)) + [months]
    animation = FuncAnimation(fig, update, frames=frames, interval=30, repeat=False)
    return axes, animation, update, set_scale


# ---------- 창 ----------

def build_window():
    """입력 칸이 달린 창을 만든다. 값을 넣고 [실행]을 눌러야 그린다.

    첫 화면에는 블랙홀이 두 개 나온다.
    왼쪽은 일정한 수익률, 오른쪽은 실제 데이터.
    왼쪽을 누르면 일정한 수익률로 계산하는 여러 모형이 펼쳐진다.
    """
    fig = plt.figure(figsize=(14, 7.5))
    fig.patch.set_facecolor("black")

    # 입력 칸: (이름, 처음 값, 왼쪽 위치, 너비)
    fields = [
        ("월 금액", "200", 0.08, 0.07),
        ("투자 비율(%)", "80", 0.25, 0.05),
        ("기간(년)", "30", 0.38, 0.05),
        ("수익률(%)", "10", 0.52, 0.05),
    ]
    boxes = {}
    for name, initial, left, width in fields:
        box = TextBox(fig.add_axes([left, 0.04, width, 0.04]), name + " ", initial=initial)
        box.label.set_color("white")
        box.label.set_fontsize(11)
        boxes[name] = box

    button = Button(fig.add_axes([0.62, 0.04, 0.07, 0.04]), "실행")
    zoom_button = Button(fig.add_axes([0.71, 0.04, 0.09, 0.04]), "각각 확대")
    back_button = Button(fig.add_axes([0.82, 0.04, 0.09, 0.04]), "돌아가기")
    back_button.ax.set_visible(False)
    message = fig.text(0.5, 0.1, HELP, color="white", fontsize=11, ha="center")

    state = {"axes": [], "animation": None, "update": None, "set_scale": None,
             "zoom": False, "detail": False, "data": None}

    def show_message(text, color):
        message.set_text(text)
        message.set_color(color)
        fig.canvas.draw_idle()

    def show():
        """지금 고른 화면을 처음부터 다시 그린다."""
        if state["animation"] is not None:
            state["animation"].event_source.stop()
        for ax in state["axes"]:
            ax.remove()

        paid, results, actual, years, headline = state["data"]
        if state["detail"]:
            # 펼친 화면: 일정한 수익률로 계산하는 모형 전부
            shown = results
            columns = COLUMNS
        else:
            # 첫 화면: 일정한 수익률 하나와 실제 데이터 하나
            note, amounts, yearly = results["입력한 수익률"]
            shown = {
                "일정한 수익률": (note + "  (누르면 여러 모형이 펼쳐집니다)", amounts, yearly),
                "실제 데이터": actual,
            }
            columns = 2
        back_button.ax.set_visible(state["detail"])

        state["axes"], state["animation"], state["update"], state["set_scale"] = draw(
            fig, paid, shown, years, headline, columns)
        state["set_scale"](state["zoom"])
        fig.canvas.draw_idle()

    def run(event=None):
        try:
            income = float(boxes["월 금액"].text)
            ratio = float(boxes["투자 비율(%)"].text)
            years = int(float(boxes["기간(년)"].text))
            my_rate = float(boxes["수익률(%)"].text)
        except ValueError:
            show_message("숫자로 입력해 주세요.", LOSS_COLOR)
            return
        if years < 1 or years > len(SP500_ACTUAL):
            show_message(f"기간은 1년부터 {len(SP500_ACTUAL)}년까지 넣을 수 있습니다. "
                         "실제 데이터가 그만큼만 있습니다.", LOSS_COLOR)
            return
        show_message(HELP, "white")

        monthly = income * ratio / 100
        paid, results, actual = calculate(monthly, years, my_rate)
        table = dict(results)
        table["실제 데이터"] = actual
        print_table(paid, table, years)

        headline = f"월 {income:g} 가운데 {ratio:g}%인 {monthly:g}씩 투자"
        state["data"] = (paid, results, actual, years, headline)
        state["detail"] = False
        show()

    def open_detail(event):
        """첫 화면에서 왼쪽 블랙홀을 누르면 여러 모형을 펼친다."""
        if state["data"] is None or state["detail"]:
            return
        if event.inaxes is state["axes"][0]:
            state["detail"] = True
            show()

    def go_back(event=None):
        if state["data"] is None or not state["detail"]:
            return
        state["detail"] = False
        show()

    def toggle_zoom(event=None):
        """같은 눈금으로 견주기와, 칸마다 확대해서 모양 보기를 오간다."""
        state["zoom"] = not state["zoom"]
        if state["zoom"]:
            zoom_button.label.set_text("같은 눈금")
        else:
            zoom_button.label.set_text("각각 확대")
        if state["set_scale"] is not None:
            state["set_scale"](state["zoom"])
        fig.canvas.draw_idle()

    button.on_clicked(run)
    zoom_button.on_clicked(toggle_zoom)
    back_button.on_clicked(go_back)
    fig.canvas.mpl_connect("button_press_event", open_detail)

    widgets = (boxes, button, zoom_button, back_button)
    actions = {"run": run, "open_detail": open_detail, "go_back": go_back, "toggle_zoom": toggle_zoom}
    return fig, widgets, state, actions


def main():
    window = build_window()  # 창을 닫을 때까지 입력 칸과 버튼이 살아 있어야 한다.
    try:
        window[0].canvas.manager.window.state("zoomed")  # 창을 화면에 꽉 채운다.
    except Exception:
        pass
    plt.show()


if __name__ == "__main__":
    main()
