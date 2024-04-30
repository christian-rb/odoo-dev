import { Component } from "@odoo/owl";

export class SpreadsheetFavorite extends Component {
    static template = "spreadsheet_edition.SpreadsheetFavorite";
    static props = {
        isFavorited: Boolean,
        onFavoriteToggled: Function,
    };
    toggleFavorite() {
        this.props.onFavoriteToggled();
    }
}
