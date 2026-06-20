"""
UAV flight-line planner - QGIS Processing script.

Draw an AOI polygon, generate flight lines, export to KML, load Waypoints onto the map.
Qgis wrapper over the pip-installed uavplanner package.

INSTALL
  1. Clone the repo.
  2. In QGIS's Python (Python Console):
       import pip; pip.main(["install", "-e", r"path-to-cloned-repo"])
     (pulls shapely, pyproj, simplekml). Restart QGIS.
  3. Processing Toolbox > Scripts > Add Script to Toolbox...  (pick this file)
"""

import os
import tempfile

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterCrs,
    QgsProcessingParameterEnum,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFileDestination,
    QgsVectorFileWriter,
    QgsFeatureRequest,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
)

# Try to import the main module
try:
    from uavplanner.planner import plan_mission
    from uavplanner.reader import read_polygon
    from uavplanner.planner_types import MissionParams
    from uavplanner.writer import write_kml
except ImportError as exc:
    raise ImportError(
        "uavplanner is not installed in QGIS's Python. Clone the repo and run, "
        "in the QGIS Python Console:\n"
        "    import pip; pip.main(['install', '-e', r'<path-to-cloned-repo>'])\n"
        "then restart QGIS and re-add this script."
    ) from exc


class PlanFlightLines(QgsProcessingAlgorithm):

    AOI = "AOI"
    ALTITUDE = "ALTITUDE"
    VELOCITY = "VELOCITY"
    FOV = "FOV"
    AUTO_AZIMUTH = "AUTO_AZIMUTH"
    AZIMUTH = "AZIMUTH"
    OVERLAP = "OVERLAP"
    LEAD_IN = "LEAD_IN"
    PRF = "PRF"
    CRS = "CRS"
    MISSION = "MISSION"
    RESTRICTED = "RESTRICTED"
    OUTPUT = "OUTPUT"

    MISSION_TYPES = ["single_grid", "double_grid"]

    # --- inputs --------------------------------------------------------------
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.AOI, "Area of interest", [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(QgsProcessingParameterNumber(
            self.ALTITUDE, "Altitude (m)",
            type=QgsProcessingParameterNumber.Double, minValue=0.0, defaultValue=70.0))

        self.addParameter(QgsProcessingParameterNumber(
            self.VELOCITY, "Velocity (m/s)",
            type=QgsProcessingParameterNumber.Double, minValue=0.0, defaultValue=5.0))

        self.addParameter(QgsProcessingParameterNumber(
            self.FOV, "Field of view (deg)",
            type=QgsProcessingParameterNumber.Double, minValue=0.0, maxValue=180.0, defaultValue=60.0))

        self.addParameter(QgsProcessingParameterBoolean(
            self.AUTO_AZIMUTH, "Auto azimuth (shortest path)", defaultValue=True))

        self.addParameter(QgsProcessingParameterNumber(
            self.AZIMUTH, "Flight azimuth (deg, used only when auto is off)",
            type=QgsProcessingParameterNumber.Double, minValue=-359.999, maxValue=359.999, defaultValue=0.0))

        self.addParameter(QgsProcessingParameterNumber(
            self.OVERLAP, "Overlap (fraction 0..1)",
            type=QgsProcessingParameterNumber.Double,
            minValue=0.0, maxValue=0.999, defaultValue=0.05))

        self.addParameter(QgsProcessingParameterNumber(
            self.LEAD_IN, "Lead-in distance (m)",
            type=QgsProcessingParameterNumber.Double, minValue=0.0, defaultValue=0.0))

        self.addParameter(QgsProcessingParameterNumber(
            self.PRF, "PRF (Hz)",
            type=QgsProcessingParameterNumber.Double, minValue=0.0, defaultValue=300000.0))

        self.addParameter(QgsProcessingParameterCrs(
            self.CRS, "Projected CRS for computation (blank = auto UTM)",
            defaultValue=None, optional=True))

        self.addParameter(QgsProcessingParameterEnum(
            self.MISSION, "Mission type", options=self.MISSION_TYPES, defaultValue=0))

        self.addParameter(QgsProcessingParameterBoolean(
            self.RESTRICTED, "Restrict airspace so flight doesnt leave AOI", defaultValue=False))

        self.addParameter(QgsProcessingParameterFileDestination(
            self.OUTPUT, "Flight lines (KML)", fileFilter="KML files (*.kml)"))

    # --- processing --------------------------------------------------------------
    def processAlgorithm(self, parameters, context, feedback):
        # 1) read every parameter back out --------------------------------------
        # Optional projected CRS: blank -> auto UTM (epsg=None). Reject geographic.
        crs = self.parameterAsCrs(parameters, self.CRS, context)
        epsg = None
        if crs.isValid():
            if crs.isGeographic():
                raise QgsProcessingException(
                    "Pick a projected CRS (metres) or leave blank for auto UTM; "
                    f"{crs.authid()} is geographic.")
            authid = crs.authid()
            epsg = int(authid.split(":")[1]) if authid.startswith("EPSG:") else crs.postgisSrid()

        auto_az = self.parameterAsBool(parameters, self.AUTO_AZIMUTH, context)
        flight_azimuth = None if auto_az else self.parameterAsDouble(parameters, self.AZIMUTH, context)

        restricted = self.parameterAsBool(parameters, self.RESTRICTED, context)
        lead_in = self.parameterAsDouble(parameters, self.LEAD_IN, context)
        if restricted and lead_in > 0:
            raise QgsProcessingException(
                "Lead-in extends lines beyond the AOI; not allowed with restricted.")

        mission_idx = self.parameterAsEnum(parameters, self.MISSION, context)

        params = MissionParams(
            altitude=self.parameterAsDouble(parameters, self.ALTITUDE, context),
            velocity=self.parameterAsDouble(parameters, self.VELOCITY, context),
            fov=self.parameterAsDouble(parameters, self.FOV, context),
            flight_azimuth=flight_azimuth,
            overlap=self.parameterAsDouble(parameters, self.OVERLAP, context),
            lead_in=lead_in,
            epsg=epsg,
            prf=self.parameterAsDouble(parameters, self.PRF, context),
            mission_type=self.MISSION_TYPES[mission_idx],
            restricted=restricted,
        )

        # translate qgis aoi to geojson
        source = self.parameterAsSource(parameters, self.AOI, context)
        if source is None:
            raise QgsProcessingException("No area of interest provided.")

        if source.featureCount() > 1:
            feedback.pushWarning("AOI has multiple features; using the first.")

        first = None
        for feat in source.getFeatures():
            first = feat
            break
        if first is None or not first.hasGeometry():
            raise QgsProcessingException("AOI feature has no geometry.")
        geom = first.geometry()
        if geom.isMultipart() and sum(1 for _ in geom.parts()) > 1:
            raise QgsProcessingException("AOI must be a single polygon (got a multipart geometry).")

        tmp_dir = tempfile.mkdtemp(prefix="uavplanner_")
        aoi_path = os.path.join(tmp_dir, "aoi.geojson")

        save_opts = QgsVectorFileWriter.SaveVectorOptions()
        save_opts.driverName = "GeoJSON"
        # read_polygon expects lon/lat (WGS84); always reproject the AOI there.
        save_opts.ct = QgsCoordinateTransform(
            source.sourceCrs(), QgsCoordinateReferenceSystem("EPSG:4326"),
            context.transformContext())
        err, msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
            source.materialize(QgsFeatureRequest()),
            aoi_path, context.transformContext(), save_opts)
        if err != QgsVectorFileWriter.NoError:
            raise QgsProcessingException(f"Could not write AOI GeoJSON: {msg}")
        feedback.pushInfo(f"AOI written to {aoi_path}")

        if feedback.isCanceled():
            return {}

        # --- run -----------------------------------------------------
        polygon = read_polygon(aoi_path)
        plan = plan_mission(polygon, params)
        feedback.pushInfo(f"Planned mission — metrics: {plan.metrics}")

        # --- write KML -----------------------------------------------
        kml_path = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        write_kml(plan, kml_path)

        # --- load to map ---------------------------------------------
        details = QgsProcessingContext.LayerDetails("Flight lines", context.project(), self.OUTPUT)
        context.addLayerToLoadOnCompletion(kml_path, details)

        return {self.OUTPUT: kml_path}

    # --- identity --------------------------------------------------------------
    def name(self):
        return "planflightlines"

    def displayName(self):
        return "Plan flight lines"

    def group(self):
        return "UAV planning"

    def groupId(self):
        return "uavplanning"

    def shortHelpString(self):
        return "Generates drone flight lines for a drawn AOI and exports them to KML."

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return PlanFlightLines()
