import { registry } from "@web/core/registry";

function _mockGetShowAllCalendarsFilter(params) {
    // When there are no records to be shown: the Everybody's calendar filter is false.
    return false;
}

function _mockGetShowOwnCalendarFilter(params) {
    // When there are no records to be shown: the own calendar filter is true.
    return true;
}

function _mockGetCalendarPartnerIds(params) {
    // When there are no records to be shown: the list of partner ids to be filtered is empty.
    return [];
}

// Add the mock functions to the sample server. This way, we can switch to the list view when the records are empty.
registry.category("sample_server").add("get_show_all_calendars_filter", _mockGetShowAllCalendarsFilter);
registry.category("sample_server").add("get_show_own_calendar_filter", _mockGetShowOwnCalendarFilter);
registry.category("sample_server").add("get_selected_calendars_partner_ids", _mockGetCalendarPartnerIds);
