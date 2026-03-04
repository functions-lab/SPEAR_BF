class PlotFormat():
    def __init__(self, scaleX=1, scaleY=1):
        self.colorList = \
            ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple',
             'tab:brown', 'tab:pink', 'tab:grey', 'tab:olive', 'tab:cyan']
        self.colorGhost = 'black'

        self.figSizeX = 5 * scaleX
        self.figSizeY = 4 * scaleY
        self.axPosX = 0.95 / self.figSizeX
        self.axPosY = 0.80 / self.figSizeY
        self.axSizeX = 1 - 1.2 / self.figSizeX
        self.axSizeY = 1 - 1.2 / self.figSizeY

        self.lineWidth = 2
        self.lineStyleList = ['solid', 'dashed', 'dashdot', 'dotted']

        self.markerList = ['o', 'v', '*', 's', 'd', 'o', 'v', '*', 's', 'd']
        self.markerSizeList = [12, 12, 12, 12, 12, 12, 12, 12, 12, 12]

        self.fontLabel = 24
        self.fontTick = 20
        self.fontTitle = 24
        self.fontLegend = 20

        self.barWidth = 0.2
