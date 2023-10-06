from odoo.http import Controller, request, route

from .user_agents import NETWORK_TO_AGENT
from ..utils.image_utils import scale_image

class SocialShareController(Controller):

    @route(['/snshare/<int:campaign_id>/card.png', '/snshare/<int:campaign_id>/<string:uid>/card.png'], type='http', auth='public', sitemap=False, website=True)
    def snshare_campaign_image(self, campaign_id=0, uid=None, small=False):
        campaign_sudo = request.env['snshare.campaign'].sudo().browse(campaign_id).exists()
        url_sudo = request.env['snshare.url']
        target = None
        if campaign_sudo.model_id:
            if not uid:
                return request.not_found()
            url_sudo = request.env['snshare.url'].sudo().search([('campaign_id', '=', campaign_sudo.id), ('uuid', '=', uid)])
            target = request.env[campaign_sudo.model_id.model].sudo().browse(url_sudo.res_id).exists()

        crawler = self._get_crawler_name(request)
        if crawler:
            request.env['bus.bus']._sendone(f'snshare_url_target-{uid}', 'snshare/share_url_target', {
                'message': campaign_sudo.thanks_message,
                'reward_url': campaign_sudo.thanks_redirection,
            })
            url_sudo.shared = True

        image_bytes = url_sudo._get_image_bytes() if url_sudo else campaign_sudo._get_images_bytes(record=target)[0]
        image_bytes = image_bytes if not small else scale_image(image_bytes, 0.5)
        return request.make_response(image_bytes, [('Content-Type', ' image/png')])

    @route(['/snshare/campaign/<int:campaign_id>', '/snshare/campaign/<int:campaign_id>/<string:uid>'], type='http', auth='public', sitemap=False, website=True)
    def snshare_campaign_visitor(self, campaign_id=0, uid=None):
        """Route for users to preview their card and share it on their social platforms."""
        campaign = request.env['snshare.campaign'].sudo().browse(campaign_id).exists()

        if not campaign:
            return request.not_found()

        target = None

        url = request.env['snshare.url']
        if campaign.model_id:
            if not uid:
                return request.not_found()
            url = request.env['snshare.url'].sudo().search([('campaign_id', '=', campaign.id), ('uuid', '=', uid)])
            url.visited = True
            target = request.env[campaign.model_id.model].sudo().browse(url.res_id).exists()
            if not target:
                return request.not_found()

        return request.render('social_share.share_campaign_visitor', {
            'image_url': self._get_card_url(campaign, uid, small=True),
            'link_shared_message': campaign.thanks_message if url.shared else '',
            'link_shared_reward_url': campaign.thanks_redirection if url.shared else '',
            'post_text': campaign.post_suggestion,
            'redirect_url': self._get_redirect_url(campaign, uid),
            'share_url': self._get_redirect_url(campaign, uid),
            'target_name': target.display_name if target else '',
            'uuid': uid,
        })

    @route(['/snshare/redirect/<int:campaign_id>', '/snshare/redirect/<int:campaign_id>/<string:uid>'], type='http', auth='public', sitemap=False, website=True)
    def snshare_campaign_redirect(self, campaign_id=0, uid=None):
        """Route to redirect users to the target url, or display the opengraph embed text for web crawlers."""
        campaign = request.env['snshare.campaign'].sudo().browse(campaign_id).exists()
        if not campaign:
            return request.not_found()
        target = False

        url = request.env['snshare.url']
        if campaign.model_id:
            if not uid:
                return request.not_found()
            url = request.env['snshare.url'].sudo().search([('campaign_id', '=', campaign.id), ('uuid', '=', uid)])
            target = request.env[campaign.model_id.model].sudo().browse(url.res_id).exists()
            if not target:
                return request.not_found()

        redirect_url = campaign.target_url_redirected

        crawler = self._get_crawler_name(request)
        if crawler:
            return request.render('social_share.share_campaign_crawler', {
                'image_url': self._get_card_url(campaign, uid),
                'target_name': target.name if target and 'name' in target else '',
                'post_text': campaign.post_suggestion,
            })

        return request.redirect(redirect_url)

    @staticmethod
    def _get_crawler_name(request):
        """Return the name of the social network for the user agent, if any."""
        user_agent = request.httprequest.user_agent.string
        for social_network, agent_names in NETWORK_TO_AGENT.items():
            if any(agent_name in user_agent for agent_name in agent_names):
                return social_network
        return ''

    @staticmethod
    def _get_card_url(share_campaign, uid, small=False):
        base = share_campaign.get_base_url()
        return f"{base}/snshare/{share_campaign.id}/{f'{uid}/' if uid else ''}card.png{'?small=1' if small else ''}"

    @staticmethod
    def _get_redirect_url(share_campaign, uid):
        base = share_campaign.get_base_url()
        return f'{base}/snshare/redirect/{share_campaign.id}' + (f'/{uid}' if uid else '')

    @staticmethod
    def _get_campaign_url(share_campaign, uid):
        base = share_campaign.get_base_url()
        return f'{base}/snshare/campaign/{share_campaign.id}' + (f'/{uid}' if uid else '')
