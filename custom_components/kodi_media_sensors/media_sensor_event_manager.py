import logging

_LOGGER = logging.getLogger(__name__)


class MediaSensorEventManager:

    _sensors = []

    def register_sensor(self, sensor):
        self._sensors.append(sensor)

    async def notify_event(self, source_entity, event):
        for sensor in self._sensors:
            if sensor._kodi == source_entity._kodi and source_entity != sensor:
                _LOGGER.debug("Notifying sensor %s", source_entity)
                await sensor.handle_media_sensor_event(event)
