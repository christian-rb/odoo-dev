/** @odoo-module **/

import { queryAttribute, queryValue, waitUntil } from '@odoo/hoot-dom';
import { TourError } from '@web_tour/tour_service/tour_utils';

function productSelector(productName) {
    return `
        table.o_sale_product_configurator_table
        tr:has(td>div[name="o_sale_product_configurator_name"]
        h5:contains("${productName}"))
    `;
}

function optionalProductSelector(productName) {
    return `
        table.o_sale_product_configurator_table_optional
        tr:has(td>div[name="o_sale_product_configurator_name"]
        h5:contains("${productName}"))
    `;
}

function optionalProductImageSrc(productName) {
    return queryAttribute(
        `${optionalProductSelector(productName)} td.o_sale_product_configurator_img>img`, 'src'
    );
}

function addOptionalProduct(productName) {
    return {
        content: `Add ${productName}`,
        trigger: `
            ${optionalProductSelector(productName)}
            td.o_sale_product_configurator_price
            button:contains("Add")
        `,
    };
}

function increaseProductQuantity(productName) {
    return {
        content: `Increase the quantity of ${productName}`,
        trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_qty
            button:has(i.fa-plus)
        `,
    };
}

function decreaseProductQuantity(productName) {
    return {
        content: `Decrease the quantity of ${productName}`,
        trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_qty
            button:has(i.fa-minus)
        `,
    };
}

function setProductQuantity(productName, quantity) {
    return {
        content: `Set the quantity of ${productName} to ${quantity}`,
        trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_qty
            input[name="product_quantity"]
        `,
        run: `edit ${quantity} && blur .modal-body`,
    };
}

function assertProductQuantity(productName, quantity) {
    const quantitySelector = `
        ${productSelector(productName)}
        td.o_sale_product_configurator_qty
        input[name="product_quantity"]
    `;
    return {
        content: `Assert that the quantity of ${productName} is ${quantity}`,
        trigger: quantitySelector,
        run: async () =>
            await waitUntil(() => queryValue(quantitySelector) === quantity, { timeout: 1000 }),
    };
}

function assertProductOutOfStock(productName) {
    return {
        content: `Assert that ${productName} is out of stock`,
        trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_qty:contains("Out of stock")
        `,
        extra_trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_qty:not(:has(input[name="product_quantity"]))
        `,
        isCheck: true,
    };
}

function assertOptionalProductOutOfStock(productName) {
    return {
        content: `Assert that ${productName} is out of stock`,
        trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_price:contains("Out of stock")
        `,
        extra_trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_price:not(:has(button:contains("Add")))
        `,
        isCheck: true,
    };
}

function selectAttribute(productName, attributeName, attributeValue, attributeType='radio') {
    const ptalSelector = `
        ${productSelector(productName)}
        td>div[name="ptal"]:has(label:contains("${attributeName}"))
    `;
    const content = `Select ${attributeValue} for ${productName} ${attributeName}`;
    switch (attributeType) {
        case 'color':
            return {
                content: content,
                trigger: `${ptalSelector} label[title="${attributeValue}"]`,
            };
        case 'multi':
        case 'pills':
        case 'radio':
            return {
                content: content,
                trigger: `${ptalSelector} span:contains("${attributeValue}")`,
            };
        case 'select':
            return {
                content: content,
                trigger: `${ptalSelector} select`,
                run: `selectByLabel ${attributeValue}`,
            };
        default:
            throw new TourError("Unsupported attribute type");
    }
}

function setCustomAttribute(productName, attributeName, customValue) {
    return {
        content: `Set ${customValue} as a custom attribute for ${productName} ${attributeName}`,
        trigger: `
            ${productSelector(productName)}
            td>div[name="ptal"]:has(label:contains("${attributeName}"))
            input[type="text"]
        `,
        run: `edit ${customValue} && blur .modal-body`,
    };
}

function selectAndSetCustomAttribute(
    productName, attributeName, attributeValue, customValue, attributeType='radio'
) {
    return [
        selectAttribute(productName, attributeName, attributeValue, attributeType),
        setCustomAttribute(productName, attributeName, customValue),
    ]
}

function assertPriceTotal(total) {
    return {
        content: `Assert that the total is ${total}`,
        trigger:
            `table.o_sale_product_configurator_table tr>td[colspan="4"] span:contains("${total}")`,
        isCheck: true,
    };
}

function assertProductPrice(productName, price) {
    return {
        content: `Assert that ${productName} costs ${price}`,
        trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_price
            h5:contains("${price}")
        `,
        isCheck: true,
    };
}

function assertOptionalProductPrice(productName, price) {
    return {
        content: `Assert that ${productName} costs ${price}`,
        trigger: `
            ${optionalProductSelector(productName)}
            td.o_sale_product_configurator_qty
            h5:contains("${price}")
        `,
        isCheck: true,
    };
}

function assertProductStrikethroughPrice(productName, price) {
    return {
        content: `Assert that ${productName} was reduced from ${price}`,
        trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_price
            h5.oe_striked_price:contains("${price}")
        `,
        isCheck: true,
    };
}

function assertOptionalProductStrikethroughPrice(productName, price) {
    return {
        content: `Assert that ${productName} was reduced from ${price}`,
        trigger: `
            ${optionalProductSelector(productName)}
            td.o_sale_product_configurator_qty
            h5.oe_striked_price:contains("${price}")
        `,
        isCheck: true,
    };
}

function assertProductPriceInfo(productName, priceInfo) {
    return {
        content: `Assert that the price info of ${productName} is ${priceInfo}`,
        trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_price
            span:contains("${priceInfo}")
        `,
        isCheck: true,
    };
}
function assertOptionalProductPriceInfo(productName, priceInfo) {
    return {
        content: `Assert that the price info of ${productName} is ${priceInfo}`,
        trigger: `
            ${optionalProductSelector(productName)}
            td.o_sale_product_configurator_qty
            span:contains("${priceInfo}")
        `,
        isCheck: true,
    };
}

function assertProductZeroPriced(productName) {
    return {
        content: `Assert that ${productName} is zero-priced`,
        trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_qty:contains("Not available for sale")
        `,
        extra_trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_qty:not(:has(input[name="product_quantity"]))
        `,
        isCheck: true,
    };
}

function assertOptionalProductZeroPriced(productName) {
    return {
        content: `Assert that ${productName} is zero-priced`,
        trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_price:contains("Not available for sale")
        `,
        extra_trigger: `
            ${productSelector(productName)}
            td.o_sale_product_configurator_price:not(:has(button:contains("Add")))
        `,
        isCheck: true,
    };
}

function assertProductNameContains(productName) {
    return {
        content: `Assert that the product name contains ${productName}`,
        trigger: productSelector(productName),
        isCheck: true,
    };
}

export default {
    productSelector,
    optionalProductSelector,
    optionalProductImageSrc,
    addOptionalProduct,
    increaseProductQuantity,
    decreaseProductQuantity,
    setProductQuantity,
    assertProductQuantity,
    assertProductOutOfStock,
    assertOptionalProductOutOfStock,
    selectAttribute,
    setCustomAttribute,
    selectAndSetCustomAttribute,
    assertPriceTotal,
    assertProductPrice,
    assertOptionalProductPrice,
    assertProductStrikethroughPrice,
    assertOptionalProductStrikethroughPrice,
    assertProductPriceInfo,
    assertOptionalProductPriceInfo,
    assertProductZeroPriced,
    assertOptionalProductZeroPriced,
    assertProductNameContains,
};
