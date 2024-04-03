/** @odoo-module **/

import { reactive } from '@odoo/owl';
import { _t } from '@web/core/l10n/translation';
import { registry } from '@web/core/registry';

export const websiteSaleService = {
    dependencies: ['cartNotificationService'],

    async start(env, { cartNotificationService }) {
        const context = reactive({
            nbItemsInCart: sessionStorage.getItem('website_sale_cart_quantity')
        });
        const options = {
            async getWebsiteOptions() {
                const options = await rpc('/shop/get_website_options');
                sessionStorage.setItem('websiteSaleAddToCartAction', options.addToCartAction);
            },
            get addToCartAction() {
                const action = sessionStorage.getItem('websiteSaleAddToCartAction');
                if (!action) {
                    this.getWebsiteOptions();
                    return sessionStorage.getItem('websiteSaleAddToCartAction');
                }
                return action;
            },
        }

        async function addToCart(params, isBuyNow=false) {
            if (isBuyNow) {
                params.express = true;
            } else if (options.addToCartAction === 'stay') {
                const data = await rpc('/shop/cart/update_json', {
                    ...params,
                    display: false,
                    force_create: true,
                });
                if (data.cart_quantity && (data.cart_quantity !== parseInt($('.my_cart_quantity').text()))) {
                    updateCartNavBar(data);
                };
                _showCartNotification(data.notification_info);
                return data;
            }
            // return wUtils.sendRequest('/shop/cart/update', params);
        }

        /**
         * Updates both navbar cart
         * @param {Object} data
         */
        function updateCartNavBar(data) {
            sessionStorage.setItem('website_sale_cart_quantity', data.cart_quantity);
            $(".my_cart_quantity")
                .parents('li.o_wsale_my_cart').removeClass('d-none').end()
                .toggleClass('d-none', data.cart_quantity === 0)
                .addClass('o_mycart_zoom_animation').delay(300)
                .queue(function () {
                    $(this)
                        .toggleClass('fa fa-warning', !data.cart_quantity)
                        .attr('title', data.warning)
                        .text(data.cart_quantity || '')
                        .removeClass('o_mycart_zoom_animation')
                        .dequeue();
                });

            $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();
            $("#cart_total").replaceWith(data['website_sale.total']);
            if (data.cart_ready) {
                document.querySelector("a[name='website_sale_main_button']")?.classList.remove('disabled');
            } else {
                document.querySelector("a[name='website_sale_main_button']")?.classList.add('disabled');
            }
        }

        // TODO VCR add tracking
        // TODO VCR handle navbar from here

        function _showCartNotification(props, options = {}) {
            // Show the notification about the cart
            if (props.lines) {
                cartNotificationService.add(_t('Item(s) added to your cart'), {
                    lines: props.lines,
                    currency_id: props.currency_id,
                    ...options,
                });
            }
            if (props.warning) {
                cartNotificationService.add(_t('Warning'), {
                    warning: props.warning,
                    ...options,
                });
            }
        }

        return { addToCart };
    },
}

registry.category('services').add('website_sale', websiteSaleService);
