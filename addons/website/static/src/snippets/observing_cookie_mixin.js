/** @odoo-module **/

export const ObservingCookieWidgetMixin = {
    /**
     * Updates the element's iframe according to whether the cookies should be
     * approved (marked by `_post_processing_att` server-side).
     * `data-need-cookies-approval` is set both on the root element in case the
     * iframe is removed and recreated on the fly client-side, so that the
     * information is passed along, as well as on the iframe, which is
     * ultimately the element that will call 3rd-party cookies.
     *
     * @private
     * @param {HTMLElement} rootEl - root element of the widget.
     * @param {string} src - src to set on the iframe.
     */
    _manageIframeSrc(rootEl, src) {
        const iframeEl = rootEl.querySelector("iframe");
        if (!rootEl.dataset.needCookiesApproval) {
            iframeEl.setAttribute("src", src);
        } else {
            iframeEl.dataset.needCookiesApproval = "true";
            iframeEl.dataset.nocookieSrc ||= src;
            iframeEl.setAttribute("src", "about:blank");
            $(iframeEl).trigger("add_cookies_warning");
        }
    },
};
