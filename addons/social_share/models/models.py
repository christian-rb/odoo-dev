from odoo import models

class BaseModel(models.AbstractModel):
    _inherit = 'base'

    def _snshare_allowed_model(self):
        """Whether the model can be used as base for a social network share campaign.

        :return bool: True if allowed
        """
        return False

    def _snshare_allowed_fields(self):
        """List of fields always allowed to be used for the purposes of social network share campaigns.

        :return list[str]:
        """
        return []
