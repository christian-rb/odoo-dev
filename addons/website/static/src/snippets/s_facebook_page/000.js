odoo.define('website.s_facebook_page', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var utils = require('web.utils');
const { debounce } = require("@web/core/utils/timing");

const FacebookPageWidget = publicWidget.Widget.extend({
    selector: '.o_facebook_page',
    disabledInEditableMode: false,

    /**
     * @override
     */
    start: function () {
        this._renderIframe();

        this.resizeObserver = new ResizeObserver(debounce(this._renderIframe.bind(this), 100));
        this.resizeObserver.observe(document.querySelector("#wrapwrap"));

        return this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    destroy: function () {
        this._super.apply(this, arguments);

        this.options.wysiwyg && this.options.wysiwyg.odooEditor.observerUnactive();
        if (this.$iframe) {
            this.$iframe.remove();
        }
        this.options.wysiwyg && this.options.wysiwyg.odooEditor.observerActive();
        this.resizeObserver.disconnect();
    },
    /**
     * _renderIframe: prepare iframe element & replace it with existing iframe
     *
     * @private
    */
    _renderIframe: function () {
        this.options.wysiwyg && this.options.wysiwyg.odooEditor.observerUnactive();

        const params = _.pick(this.$el[0].dataset, 'href', 'id', 'height', 'tabs', 'small_header', 'hide_cover');
        if (!params.href) {
            return;
        }
        if (params.id) {
            params.href = `https://www.facebook.com/${params.id}`;
        }
        delete params.id;
        params.width = utils.confine(Math.floor(this.$el.width()), 180, 500);

        var src = $.param.querystring('https://www.facebook.com/plugins/page.php', params);
        const iframeEl = Object.assign(document.createElement("iframe"), {
            src: src,
            width: params.width,
            height: params.height,
            css: {
                border: 'none',
                overflow: 'hidden',
            },
            scrolling: 'no',
            frameborder: '0',
            allowTransparency: 'true',
        });
        this.el.replaceChildren(iframeEl);

        this.options.wysiwyg && this.options.wysiwyg.odooEditor.observerActive();
    },
});

publicWidget.registry.facebookPage = FacebookPageWidget;

return FacebookPageWidget;
});
