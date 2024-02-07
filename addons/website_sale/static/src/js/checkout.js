/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { renderToElement } from "@web/core/utils/render";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.websiteSaleCheckout = publicWidget.Widget.extend({
    // /shop/checkout
    selector: '#shop_checkout',
    events: {
        // addresses
        'click .js_change_billing': '_changeBillingAddress',
        'click .js_change_shipping': '_changeShippingAddress',
        'click .js_edit_address': '_editAddress',
        // delivery
        'click [name="o_delivery_radio"]': '_selectDeliveryCarrier',
        "click .o_address_select": "_selectLocation",
        "click .o_remove_order_location": "_removeLocation",
    },

    async start(){
        this.mainButton = document.querySelector('a[name="website_sale_main_button"]');
        await this._prepareDeliveryCarriers();
    },

    //--------------------------------------------------------------------------
    // Event handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} ev
     */
    async _changeBillingAddress (ev) {
        await this._changeAddress(ev, 'all_billing', 'js_change_billing');
    },

    /**
     * @private
     * @param {Event} ev
     */
    async _changeShippingAddress (ev) {
        await this._changeAddress(ev, 'all_shipping', 'js_change_shipping');
    },

    /**
     * @private
     * @param {Event} ev
     */
    async _changeAddress(ev, rowAddrClass, cardClass) {
        const oldCard = document.querySelector(`.${rowAddrClass}`).querySelector(
            '.card.border.border-primary'
        );
        oldCard.classList.add(cardClass);
        oldCard.classList.remove('bg-primary', 'border', 'border-primary');

        const newCard = ev.currentTarget.closest('div.one_kanban').querySelector('.card');
        newCard.classList.remove(cardClass);
        newCard.classList.add('bg-primary', 'border', 'border-primary');
        const mode = newCard.getAttribute('mode');
        await rpc(
            '/shop/cart/update_address',
            {
                mode: mode,
                partner_id: newCard.getAttribute('partner_id'),
            }
        )
        // When shipping address is changed, update available delivery carriers
        if (mode === 'shipping'){
            document.getElementById('o_delivery_form').innerHTML = await rpc(
                '/shop/delivery_carriers'
            );
            await this._prepareDeliveryCarriers();
        }
    },

    /**
     * @private
     * @param {Event} ev
     */
    _editAddress(ev) {
        // Do not trigger _onClickChangeBilling or _onClickChangeShipping when customer
        // clicks on the pencil to update the address
        ev.stopPropagation();
    },

    /**
     * @private
     * @param {Event} ev
     */
    async _selectDeliveryCarrier(ev) {
        const radio = ev.currentTarget;
        if (radio.disabled) return; // rate shipment request failed
        this._disableMainButton();
        this._hideOrderPickupLocations();
        this._showLoadingBadge(radio);
        const result = await this._getResultUpdateCarrier(radio.value);
        this._updateAmountBadge(radio, result);
        this._updateCartSummary(result);
        this._enableButton();
        await this._showClosestPickupLocations(radio);
    },

    /**
     * @private
     * @param {Event} ev
     */
    async _selectLocation(ev) {
        ev.stopPropagation();
        const carrierContainer = this._getCarrierContainer(ev.currentTarget);
        const radio = carrierContainer.querySelector('input[type="radio"]');
        const listPickupLocations = this._getListPickupLocations(carrierContainer);
        const encodedLocation = ev.target.previousElementSibling.innerText;
        await this._setAccessPoint(encodedLocation);
        this._clearElement(listPickupLocations);
        await this._showOrderAccessPoint(radio);
        this._enableButton();
    },

    /**
     * @private
     */
    async _removeLocation(ev) {
        ev.stopPropagation();
        this._disableMainButton();
        await this._setAccessPoint(null);
        const radio = this._getCarrierContainer(ev.currentTarget).querySelector(
            'input[type="radio"]'
        );
        await this._showOrderAccessPoint(radio);
        await this._showClosestPickupLocations(radio);
    },

    //--------------------------------------------------------------------------
    // Delivery flow
    //--------------------------------------------------------------------------

    async _prepareDeliveryCarriers() {
        this.carrierRadios = Array.from(
            document.querySelectorAll('input[name="o_delivery_radio"]')
        );
        if (this.carrierRadios.length > 0) {
            const carrierChecked = document.querySelector(
                'input[name="o_delivery_radio"]:checked'
            );
            this._disableMainButton();
            if (carrierChecked) {
                const result = await this._getResultUpdateCarrier(carrierChecked.value);
                this._updateAmountBadge(carrierChecked, result);
                this._updateCartSummary(result);
                await this._showOrderAccessPoint(carrierChecked);
                this._enableButton();
                await this._showClosestPickupLocations(carrierChecked);
            }
        }
        // asynchronously request rates to mitigate delays from third-party APIs
        // load and display amount in badges
        await Promise.all(this.carrierRadios.filter((radio) => !radio.checked).map(async (radio) =>{
            this._showLoadingBadge((radio));
            const res = await this._getCarrierRateShipment(radio);
            this._updateAmountBadge(radio, res);
        }));
    },

    /**
     * Fetch and display close pickup locations to order shipping address.
     *
     * @private
     * @params {Element} radio: The carrier radio element.
     */
    async _showClosestPickupLocations(radio) {
        this._hideListLocations();
        const carrierContainer = this._getCarrierContainer(radio);
        if (!this._pickupShouldBeSelected(radio) || radio.disabled) {
            return;
        }
        const listPickUpLocations = this._getListPickupLocations(carrierContainer);
        const title = document.createElement("div");
        title.classList.add("h6", "m-3");
        title.textContent = _t("Please select a pick-up point");
        title.style = "color:red;";
        listPickUpLocations.append(title);
        const deliveryType = radio.getAttribute("delivery_type");
        listPickUpLocations.appendChild(this._getLoadingElement()) // add loading element
        const data = await rpc("/shop/order_access_point/close_locations");
        this._clearElement(listPickUpLocations); // remove loading element
        if (data.error) {
            const errorMessage = document.createElement("em");
            errorMessage.innerText = data.error
            listPickUpLocations.appendChild(errorMessage);
            return;
        }
        // corresponding delivery carrier template to render pickup locations
        const templateToRender = deliveryType + "_pickup_location_list";
        const context = {
            partner_address: data.partner_address,
            pickup_locations: data.close_locations,
        };
        listPickUpLocations.append(renderToElement(templateToRender, context));
    },

    /**
     * Show order pickup point if selected.
     *
     * @private
     * @params {Element} radio: The carrier radio element.
     */
    async _showOrderAccessPoint(radio) {
        if (!this._getIsPickupNeeded(radio)){
            return
        }
        const data = await rpc("/shop/order_access_point/get");
        const carrierContainer = this._getCarrierContainer(radio);
        const orderLoc = carrierContainer.querySelector('.o_order_location');
        const access_point = data['pickup_address'];
        orderLoc.querySelector(".o_order_location_name").innerText = data.name || '';
        orderLoc.querySelector(".o_order_location_address").innerText = access_point || '';
        if (access_point) {
            orderLoc.classList.remove("d-none");
        } else {
            orderLoc.classList.add("d-none");
        }
    },

    /**
     * Check if the delivery carrier is selected and a pickup point is selected if needed.
     *
     * @private
     * @return {boolean}
     */
    _isCarrierReady() {
        if (this.carrierRadios.length === 0) { // No carrier is available.
            return true; // Ignore the check.
        }
        const checked = document.querySelector('input[name="o_delivery_radio"]:checked');
        return checked && !checked.disabled && !this._pickupShouldBeSelected(checked);
    },

    /**
     * Check if a pickup point is required but not selected.
     *
     * @private
     * @params {Element} radio: The carrier radio element.
     */
    _pickupShouldBeSelected(radio) {
        const carrierContainer = this._getCarrierContainer(radio);
        const address = carrierContainer.querySelector('.o_order_location_address').innerText;
        return this._getIsPickupNeeded(radio) && address === '';
    },

    //--------------------------------------------------------------------------
    // DOM manipulation
    //--------------------------------------------------------------------------

    _showLoadingBadge: function (radio) {
        const priceTag = this._getCarrierBadge(radio);
        this._clearElement(priceTag);
        priceTag.appendChild(this._getLoadingElement());
    },

    /**
     * @private
     * @params {Object} result: The order summary values.
     */
    _updateCartSummary(result) {
        const amountDelivery = document.querySelector('#order_delivery .monetary_field');
        const amountUntaxed = document.querySelector('#order_total_untaxed .monetary_field');
        const amountTax = document.querySelector('#order_total_taxes .monetary_field');
        const amountTotal = document.querySelectorAll(
            '#order_total .monetary_field, #amount_total_summary.monetary_field'
        );

        amountDelivery.innerHTML = result.amount_delivery;
        amountUntaxed.innerHTML = result.amount_untaxed;
        amountTax.innerHTML = result.amount_tax;
        amountTotal.forEach(total => total.innerHTML = result.amount_total);
    },

    /**
     * @private
     * @params {Element} radio: The carrier radio element.
     * @params {Object} rate: The rate of shipment.
     */
    _updateAmountBadge(radio, rate) {
        const carrierBadge = this._getCarrierBadge(radio);
        const carrierContainer = this._getCarrierContainer(radio)
        if (rate.success) {
             // if free delivery (`free_over` field), show 'Free', not '$0'
             if (rate.is_free_delivery) {
                 carrierBadge.textContent = _t('Free');
             } else {
                 carrierBadge.innerHTML = rate.amount_delivery;
             }
             radio.disabled = false;
             carrierContainer.classList.remove('text-muted');
        } else {
            carrierBadge.textContent = rate.error_message;

            radio.disabled = true; // disable radio if there is an error
            carrierContainer.classList.add('text-muted');
        }
    },

    /**
     * @private
     * @params {Element} el: DOM element.
     */
    _clearElement(el) {
        while (el.firstChild) {
            el.removeChild(el.lastChild);
        }
    },

    /**
     * @private
     * @return {void}
     */
    _hideListLocations() {
        const listLocations = document.querySelectorAll(".o_list_pickup_locations");
        for (const loc of listLocations) {
            this._clearElement(loc);
        }
    },

    /**
     * Reset order location name and address.
     *
     * @private
     * @params {Element} radio: The carrier radio element.
     */
    _hideOrderPickupLocations() {
        const orderLocations = document.querySelectorAll(".o_order_location");
        for (const orderLoc of orderLocations) {
            orderLoc.querySelector(".o_order_location_name").innerText = '';
            orderLoc.querySelector(".o_order_location_address").innerText = '';
            orderLoc.classList.add("d-none");
        }
    },

    //--------------------------------------------------------------------------
    // Getters & setters
    //--------------------------------------------------------------------------

    /**
     * Get the rate shipment of a carrier.
     *
     * @private
     * @params {Element} radio: The carrier radio element.
     */
    async _getCarrierRateShipment(radio) {
        return await rpc('/shop/get_shipment_rate', {
            'carrier_id': radio.value,
        });
    },

    /**
     * Update the carrier on the order and get result values.
     *
     * @private
     * @params {Integer} carrier_id: The id of selected carrier.
     */
    async _getResultUpdateCarrier(carrier_id) {
        return await rpc('/shop/update_carrier', {'carrier_id': carrier_id});
    },

    /**
     * Update order access point location.
     *
     * @private
     * @params {String} accessPoint: An encoded access point location.
     */
    async _setAccessPoint(accessPoint) {
        await rpc("/shop/order_access_point/set", {
            access_point_encoded: accessPoint,
        });
    },

    _getLoadingElement() {
        const loadingElement = document.createElement('i');
        loadingElement.classList.add('fa', 'fa-circle-o-notch', 'fa-spin', 'center');
        return loadingElement;
    },

    /**
     * @private
     * @params {Element} radio: The carrier radio element.
     */
    _getIsPickupNeeded(radio) {
        return Boolean(radio.dataset['isPickupNeeded']);
    },

    /**
     * @private
     * @params {Element} radio: The carrier radio element.
     */
    _getCarrierContainer(el) {
        return el.closest('[name="o_delivery_option"]');
    },

    /**
     * @private
     * @params {Element} carrierContainer: The carrier container element.
     */
    _getListPickupLocations(carrierContainer) {
        return carrierContainer.querySelector('.o_list_pickup_locations');
    },

    /**
     * @private
     * @params {Element} radio: The carrier radio element.
     */
    _getCarrierBadge(radio) {
        return this._getCarrierContainer(radio).querySelector('.o_wsale_delivery_badge_price');
    },

    /**
     * Disable the main button.
     *
     * @private
     * @return {void}
     */
    _disableMainButton() {
        this.mainButton?.classList.add('disabled');
    },

    /**
     * Enable the main button if carrier is selected.
     *
     * @private
     * @return {void}
     */
    _enableButton(){
        if (this._isCarrierReady()) {
            this.mainButton?.classList.remove('disabled');
        }
    },

});

export default publicWidget.registry.websiteSaleCheckout;
