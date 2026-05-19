from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from app.views.styles.theme import COR, CORES_GRAFICO

FUNDO_GRAFICO = (20/255, 20/255, 31/255, 0.5)


class ChartWidget(FigureCanvasQTAgg):
    def __init__(self, titulo, width=5, height=3.2, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor(FUNDO_GRAFICO)
        super().__init__(self.fig)
        self.titulo = titulo
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(FUNDO_GRAFICO)
        self._estilo_eixos()
        self._draw_empty()

    def _estilo_eixos(self):
        self.ax.tick_params(colors=COR["texto_sec"], labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color(COR["borda"])
            spine.set_linewidth(0.5)
        self.ax.set_title(self.titulo, color=COR["texto"], fontsize=11, fontweight="bold", pad=12)

    def _draw_empty(self):
        self.ax.text(0.5, 0.5, "Sem dados", color=COR["texto_muted"], ha="center", va="center", fontsize=12)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.draw()

    def limpar(self):
        self.ax.clear()
        self.ax.set_facecolor(FUNDO_GRAFICO)
        self._estilo_eixos()


class PizzaChart(ChartWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def atualizar(self, labels, valores):
        self.limpar()
        total = sum(valores)
        if total == 0:
            self._draw_empty()
            return
        wedges, texts, autotexts = self.ax.pie(
            valores,
            labels=labels,
            autopct="%1.1f%%",
            colors=CORES_GRAFICO[: len(labels)],
            textprops={"color": COR["texto"], "fontsize": 9},
            pctdistance=0.75,
            wedgeprops={"linewidth": 1, "edgecolor": FUNDO_GRAFICO},
            startangle=90,
        )
        for t in autotexts:
            t.set_color("white")
            t.set_fontweight("bold")
        self.draw()


class BarChart(ChartWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def atualizar(self, labels, valores):
        self.limpar()
        if not valores:
            self._draw_empty()
            return
        bars = self.ax.bar(labels, valores, color=CORES_GRAFICO[: len(valores)], edgecolor=None, linewidth=0.5)
        self.ax.set_xlabel("")
        for i, (bar, v) in enumerate(zip(bars, valores)):
            self.ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3, str(v),
                         ha="center", va="bottom", color=COR["texto_sec"], fontsize=8)
        self.fig.autofmt_xdate(rotation=30, ha="right")
        self.draw()


class LineChart(ChartWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def atualizar(self, labels, valores):
        self.limpar()
        if not valores:
            self._draw_empty()
            return
        self.ax.plot(labels, valores, color=COR["roxo"], marker="o", linewidth=2, markersize=4)
        self.ax.fill_between(range(len(valores)), valores, alpha=0.1, color=COR["roxo"])
        self.ax.set_xlabel("")
        self.fig.autofmt_xdate(rotation=30, ha="right")
        self.draw()
