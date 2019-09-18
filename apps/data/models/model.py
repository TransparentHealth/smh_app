from datamodels import Model


class DataModel(Model):
    """base class for dataclass models"""

    @property
    def resourceType(self):
        return self.__class__.__name__
