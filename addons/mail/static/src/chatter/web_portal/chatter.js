import { AttachmentList } from "@mail/core/common/attachment_list";
import { Composer } from "@mail/core/common/composer";
import { Thread } from "@mail/core/common/thread";
import { useMessageHighlight } from "@mail/utils/common/hooks";
import { SearchMessagesPanel } from "@mail/core/common/search_messages_panel";

import {
    Component,
    onMounted,
    onWillUpdateProps,
    useChildSubEnv,
    useRef,
    useState,
} from "@odoo/owl";

import { Dropdown } from "@web/core/dropdown/dropdown";
import { useService } from "@web/core/utils/hooks";
import { useThrottleForAnimation } from "@web/core/utils/timing";
import { FileUploader } from "@web/views/fields/file_handler";

/**
 * @typedef {Object} Props
 * @extends {Component<Props, Env>}
 */
export class Chatter extends Component {
    static template = "mail.Chatter";
    static components = {
        AttachmentList,
        Dropdown,
        Thread,
        Composer,
        FileUploader,
        SearchMessagesPanel,
    };
    static props = ["threadId?", "threadModel"];
    static defaultProps = { threadId: false };

    setup() {
        this.action = useService("action");
        this.attachmentBox = useRef("attachment-box");
        this.threadService = useService("mail.thread");
        this.store = useState(useService("mail.store"));
        this.orm = useService("orm");
        this.messageService = useService("mail.message");
        this.state = useState({
            composerType: false,
            jumpThreadPresent: 0,
            /** @type {import("models").Thread} */
            thread: undefined,
            isSearchOpen: false,
        });
        this.rootRef = useRef("root");
        this.onScrollDebounced = useThrottleForAnimation(this.onScroll);
        this.messageHighlight = useMessageHighlight();
        useChildSubEnv({
            inChatter: true,
            messageHighlight: this.messageHighlight,
        });

        onMounted(() => {
            this.state.thread = this.store.Thread.insert({
                model: this.props.threadModel,
                id: this.props.threadId,
            });
            this.onMount();
        });
        onWillUpdateProps((nextProps) => {
            if (this.isThreadShifted) {
                this.state.thread = this.store.Thread.insert({
                    model: nextProps.threadModel,
                    id: nextProps.threadId,
                });
            }
            this.onUpdateProps(nextProps);
        });
    }

    get afterPostRequestList() {
        return ["messages"];
    }

    get requestList() {
        return [];
    }

    isThreadShifted(currentProps, nextProps) {
        return (
            currentProps.threadId !== nextProps.threadId ||
            currentProps.threadModel !== nextProps.threadModel
        );
    }

    /**
     * Fetch data for the thread according to the request list.
     * @param {import("models").Thread} thread
     * @param {string[]} requestList
     */
    load(thread, requestList) {
        if (!thread.id || !this.state.thread?.eq(thread)) {
            return;
        }
        this.threadService.fetchData(thread, requestList);
    }

    onMount() {
        if (!this.env.chatter || this.env.chatter?.fetchData) {
            if (this.env.chatter) {
                this.env.chatter.fetchData = false;
            }
            this.load(this.state.thread, this.requestList);
        }
    }

    onPostCallback() {
        this.state.jumpThreadPresent++;
        // Load new messages to fetch potential new messages from other users (useful due to lack of auto-sync in chatter).
        this.load(this.state.thread, this.afterPostRequestList);
    }

    onClickSearch() {
        this.state.composerType = false;
        this.state.isSearchOpen = !this.state.isSearchOpen;
    }

    closeSearch() {
        this.state.isSearchOpen = false;
    }

    onScroll() {
        this.state.isTopStickyPinned = this.rootRef.el.scrollTop !== 0;
    }

    onUpdateProps(nextProps) {
        if (!this.env.chatter || this.env.chatter?.fetchData) {
            if (this.env.chatter) {
                this.env.chatter.fetchData = false;
            }
            this.load(this.state.thread, this.requestList);
        }
    }
}
