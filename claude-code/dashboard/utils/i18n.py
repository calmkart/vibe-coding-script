"""Internationalization (i18n) module for the dashboard.

Provides simple dict-based translations for English and Chinese.
Use ``set_lang`` to switch language and ``t`` to retrieve translated strings.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Current language (module-level state)
# ---------------------------------------------------------------------------

_LANG: str = "en"


def set_lang(lang: str) -> None:
    """Set the active UI language.

    Args:
        lang: Language code. Supported values are ``"en"`` and ``"zh"``.
    """
    global _LANG
    _LANG = lang


def t(key: str) -> str:
    """Return the translated string for *key* in the current language.

    Falls back to English when the current language or key is missing,
    and returns the raw *key* if no translation exists at all.
    """
    translations = _TRANSLATIONS.get(_LANG) or _TRANSLATIONS["en"]
    return translations.get(key, _TRANSLATIONS["en"].get(key, key))


# ---------------------------------------------------------------------------
# English translations
# ---------------------------------------------------------------------------

_EN: dict[str, str] = {
    # Tab labels
    "tab_active": "\u25c9 Active",
    "tab_history": "\U0001f4da History",
    "tab_usage": "\U0001f4ca Usage",
    "tab_conversation": "\U0001f4ac Conversation",

    # App titles
    "app_title": "Claude Code Dashboard",
    "app_subtitle": "Session Manager",

    # Help text
    "help_title": "Claude Code Dashboard",
    "help_nav_title": "Navigation",
    "help_nav_tab": "Tab/S-Tab    Next / prev tab",
    "help_nav_num": "1-4          Switch to tab",
    "help_nav_updown": "\u2191/\u2193          Navigate items",
    "help_nav_leftright": "\u2190/\u2192          Switch panes / Period",
    "help_nav_enter": "Enter        Open / Select",
    "help_nav_escape": "Escape       Back / Close",
    "help_actions_title": "Actions",
    "help_action_iterm": "Ctrl+G       Jump to iTerm tab",
    "help_action_resume": "r            Resume session",
    "help_action_delete": "Del/Bksp     Delete session",
    "help_action_export": "e            Export to Markdown",
    "help_action_thinking": "t            Toggle thinking blocks",
    "help_action_sort": "s            Cycle sort order",
    "help_global_title": "Global",
    "help_global_search": "Ctrl+F  /    Search conversations",
    "help_global_refresh": "Ctrl+R       Refresh all data",
    "help_global_help": "?            This help",
    "help_global_quit": "q            Quit",

    # Active screen
    "active_sessions": "Active Sessions",
    "active_hint": "\u2191\u2193:Navigate  Enter:View  Ctrl+G:iTerm  r:Resume",
    "active_no_sessions": "No active sessions",
    "active_empty": "No active Claude Code sessions",
    "active_empty_hint": "Start Claude Code in a terminal to see sessions here.",
    "active_refreshing": "Auto-refreshing every 2s",
    "working": "working",
    "attention": "attention",
    "done": "done",
    "jumping_to": "Jumping to",
    "switched_to": "Switched to",

    # Status labels
    "status_working": "Working",
    "status_attention": "Attention",
    "status_done": "Done",

    # Browser screen
    "projects": "Projects",
    "sessions": "Sessions",
    "browser_hint_projects": "\u2190\u2192:Switch pane  s:Sort",
    "browser_hint_sessions": "Enter:View  r:Resume  Del:Delete  e:Export",
    "sort_label": "Sort",
    "sort_date": "Date",
    "sort_messages": "Messages",
    "sort_size": "Size",
    "no_sessions_in_project": "No sessions in this project",
    "n_sessions": "sessions",
    "delete_session_title": "Delete Session",
    "delete_confirm": "Are you sure you want to delete session",
    "delete_warning": "This action cannot be undone.",
    "cancel": "Cancel",
    "delete": "Delete",
    "resuming_session": "Resuming session",
    "in_new_tab": "in new tab",
    "deleted_session": "Deleted session",
    "failed_to_delete": "Failed to delete session",
    "exported_to": "Exported to",
    "sort_notify": "Sort",

    # Usage screen
    "usage_dashboard": "Usage & Cost Dashboard",
    "usage_no_data": "No usage data found. Start using Claude Code to see stats here.",
    "usage_hint": "\u2190\u2192:Change Period  \u2191\u2193:Scroll",
    "total_sessions": "Total Sessions",
    "total_messages": "Total Messages",
    "est_total_cost": "Est. Total Cost",
    "longest_session": "Longest Session",
    "period_all": "All Time",
    "period_30d": "Last 30 Days",
    "period_7d": "Last 7 Days",
    "period_label": "Period",
    "daily_activity": "Daily Activity",
    "model_usage_cost": "Model Usage & Estimated Cost",
    "usage_by_hour": "Usage by Hour of Day",
    "daily_token_usage": "Daily Token Usage",
    "cost_by_model": "Cost by Model",
    "cost_by_project": "Cost by Project",
    "msgs": "msgs",

    # Conversation screen
    "conv_select_hint": "Select a session from Active or History tab to view conversation",
    "conv_hint": "Esc:Back  e:Export  t:Thinking  Home/End:Top/Bottom",
    "conv_hint_short": "Esc:Back  Home/End:Top/Bottom",
    "no_session_loaded": "No session loaded",
    "no_conversation": "No conversation messages found",
    "session_empty_hint": "This session may be empty or still loading.",
    "user_role": "USER",
    "assistant_role": "ASSISTANT",
    "no_session_to_export": "No session loaded to export",
    "thinking_shown": "Thinking blocks shown",
    "thinking_hidden": "Thinking blocks hidden",
    "thinking_expand_hint": "Thinking - press 't' to expand",

    # Search
    "search_title": "Search Conversations",
    "search_esc_hint": "Esc to close",
    "search_placeholder": "Type search query and press Enter...",
    "search_no_results": "No results for",
    "search_results_for": "result(s) for",

    # Table headers
    "col_model": "Model",
    "col_input_tokens": "Input Tokens",
    "col_output_tokens": "Output Tokens",
    "col_cache_read": "Cache Read",
    "col_cache_write": "Cache Write",
    "col_est_cost": "Est. Cost",
    "col_percent": "%",
    "total": "TOTAL",

    # Heatmap
    "heatmap_title": "Session starts by hour (local time)",
    "heatmap_no_data": "No hourly data",
    "hour_period_0": "Night",
    "hour_period_6": "Morning",
    "hour_period_12": "Afternoon",
    "hour_period_18": "Evening",
    "legend_none": "none",
    "legend_low": "low",
    "legend_med": "med",
    "legend_high": "high",
    "legend_peak": "peak",

    # Chart
    "chart_no_data": "No data",

    # Misc
    "all_data_refreshed": "All data refreshed",
    "worktree_tag": "worktree",
    "in_label": "in",
    "out_label": "out",
}

# ---------------------------------------------------------------------------
# Chinese translations
# ---------------------------------------------------------------------------

_ZH: dict[str, str] = {
    # Tab labels
    "tab_active": "\u25c9 \u6d3b\u8dc3",
    "tab_history": "\U0001f4da \u5386\u53f2",
    "tab_usage": "\U0001f4ca \u7528\u91cf",
    "tab_conversation": "\U0001f4ac \u5bf9\u8bdd",

    # App titles
    "app_title": "Claude Code \u4eea\u8868\u76d8",
    "app_subtitle": "\u4f1a\u8bdd\u7ba1\u7406",

    # Help text
    "help_title": "Claude Code \u4eea\u8868\u76d8",
    "help_nav_title": "\u5bfc\u822a",
    "help_nav_tab": "Tab/S-Tab    \u4e0b\u4e00\u4e2a / \u4e0a\u4e00\u4e2a\u6807\u7b7e",
    "help_nav_num": "1-4          \u5207\u6362\u6807\u7b7e\u9875",
    "help_nav_updown": "\u2191/\u2193          \u5bfc\u822a\u5217\u8868",
    "help_nav_leftright": "\u2190/\u2192          \u5207\u6362\u9762\u677f / \u65f6\u95f4\u8303\u56f4",
    "help_nav_enter": "Enter        \u6253\u5f00 / \u9009\u62e9",
    "help_nav_escape": "Escape       \u8fd4\u56de / \u5173\u95ed",
    "help_actions_title": "\u64cd\u4f5c",
    "help_action_iterm": "Ctrl+G       \u8df3\u8f6c\u5230 iTerm \u6807\u7b7e",
    "help_action_resume": "r            \u6062\u590d\u4f1a\u8bdd",
    "help_action_delete": "Del/Bksp     \u5220\u9664\u4f1a\u8bdd",
    "help_action_export": "e            \u5bfc\u51fa\u4e3a Markdown",
    "help_action_thinking": "t            \u5207\u6362\u601d\u8003\u5757",
    "help_action_sort": "s            \u5207\u6362\u6392\u5e8f",
    "help_global_title": "\u5168\u5c40",
    "help_global_search": "Ctrl+F  /    \u641c\u7d22\u5bf9\u8bdd",
    "help_global_refresh": "Ctrl+R       \u5237\u65b0\u6570\u636e",
    "help_global_help": "?            \u5e2e\u52a9",
    "help_global_quit": "q            \u9000\u51fa",

    # Active screen
    "active_sessions": "\u6d3b\u8dc3\u4f1a\u8bdd",
    "active_hint": "\u2191\u2193:\u5bfc\u822a  Enter:\u67e5\u770b  Ctrl+G:iTerm  r:\u6062\u590d",
    "active_no_sessions": "\u6682\u65e0\u6d3b\u8dc3\u4f1a\u8bdd",
    "active_empty": "\u6682\u65e0\u6d3b\u8dc3\u7684 Claude Code \u4f1a\u8bdd",
    "active_empty_hint": "\u5728\u7ec8\u7aef\u4e2d\u542f\u52a8 Claude Code \u5373\u53ef\u5728\u6b64\u67e5\u770b\u4f1a\u8bdd\u3002",
    "active_refreshing": "\u6bcf 2 \u79d2\u81ea\u52a8\u5237\u65b0",
    "working": "\u8fd0\u884c\u4e2d",
    "attention": "\u5f85\u786e\u8ba4",
    "done": "\u5b8c\u6210",
    "jumping_to": "\u8df3\u8f6c\u5230",
    "switched_to": "\u5df2\u5207\u6362\u5230",

    # Status labels
    "status_working": "\u8fd0\u884c\u4e2d",
    "status_attention": "\u5f85\u786e\u8ba4",
    "status_done": "\u5b8c\u6210",

    # Browser screen
    "projects": "\u9879\u76ee",
    "sessions": "\u4f1a\u8bdd",
    "browser_hint_projects": "\u2190\u2192:\u5207\u6362\u9762\u677f  s:\u6392\u5e8f",
    "browser_hint_sessions": "Enter:\u67e5\u770b  r:\u6062\u590d  Del:\u5220\u9664  e:\u5bfc\u51fa",
    "sort_label": "\u6392\u5e8f",
    "sort_date": "\u65e5\u671f",
    "sort_messages": "\u6d88\u606f\u6570",
    "sort_size": "\u5927\u5c0f",
    "no_sessions_in_project": "\u8be5\u9879\u76ee\u6682\u65e0\u4f1a\u8bdd",
    "n_sessions": "\u4e2a\u4f1a\u8bdd",
    "delete_session_title": "\u5220\u9664\u4f1a\u8bdd",
    "delete_confirm": "\u786e\u5b9a\u8981\u5220\u9664\u4f1a\u8bdd",
    "delete_warning": "\u6b64\u64cd\u4f5c\u65e0\u6cd5\u64a4\u9500\u3002",
    "cancel": "\u53d6\u6d88",
    "delete": "\u5220\u9664",
    "resuming_session": "\u6b63\u5728\u6062\u590d\u4f1a\u8bdd",
    "in_new_tab": "\u5728\u65b0\u6807\u7b7e\u9875\u4e2d",
    "deleted_session": "\u5df2\u5220\u9664\u4f1a\u8bdd",
    "failed_to_delete": "\u5220\u9664\u4f1a\u8bdd\u5931\u8d25",
    "exported_to": "\u5df2\u5bfc\u51fa\u5230",
    "sort_notify": "\u6392\u5e8f",

    # Usage screen
    "usage_dashboard": "\u7528\u91cf\u4e0e\u8d39\u7528",
    "usage_no_data": "\u6682\u65e0\u4f7f\u7528\u6570\u636e\u3002\u5f00\u59cb\u4f7f\u7528 Claude Code \u5373\u53ef\u5728\u6b64\u67e5\u770b\u7edf\u8ba1\u3002",
    "usage_hint": "\u2190\u2192:\u5207\u6362\u8303\u56f4  \u2191\u2193:\u6eda\u52a8",
    "total_sessions": "\u603b\u4f1a\u8bdd\u6570",
    "total_messages": "\u603b\u6d88\u606f\u6570",
    "est_total_cost": "\u9884\u4f30\u603b\u8d39\u7528",
    "longest_session": "\u6700\u957f\u4f1a\u8bdd",
    "period_all": "\u5168\u90e8",
    "period_30d": "\u8fd1 30 \u5929",
    "period_7d": "\u8fd1 7 \u5929",
    "period_label": "\u8303\u56f4",
    "daily_activity": "\u6bcf\u65e5\u6d3b\u52a8",
    "model_usage_cost": "\u6a21\u578b\u7528\u91cf\u4e0e\u9884\u4f30\u8d39\u7528",
    "usage_by_hour": "\u6309\u65f6\u6bb5\u5206\u5e03",
    "daily_token_usage": "\u6bcf\u65e5 Token \u7528\u91cf",
    "cost_by_model": "\u6a21\u578b\u8d39\u7528\u5360\u6bd4",
    "cost_by_project": "\u6309\u9879\u76ee\u7edf\u8ba1\u8d39\u7528",
    "msgs": "\u6761\u6d88\u606f",

    # Conversation screen
    "conv_select_hint": "\u4ece\u6d3b\u8dc3\u6216\u5386\u53f2\u6807\u7b7e\u4e2d\u9009\u62e9\u4f1a\u8bdd\u67e5\u770b\u5bf9\u8bdd",
    "conv_hint": "Esc:\u8fd4\u56de  e:\u5bfc\u51fa  t:\u601d\u8003  Home/End:\u9876/\u5e95",
    "conv_hint_short": "Esc:\u8fd4\u56de  Home/End:\u9876/\u5e95",
    "no_session_loaded": "\u672a\u52a0\u8f7d\u4f1a\u8bdd",
    "no_conversation": "\u672a\u627e\u5230\u5bf9\u8bdd\u6d88\u606f",
    "session_empty_hint": "\u6b64\u4f1a\u8bdd\u53ef\u80fd\u4e3a\u7a7a\u6216\u4ecd\u5728\u52a0\u8f7d\u4e2d\u3002",
    "user_role": "\u7528\u6237",
    "assistant_role": "\u52a9\u624b",
    "no_session_to_export": "\u6ca1\u6709\u53ef\u5bfc\u51fa\u7684\u4f1a\u8bdd",
    "thinking_shown": "\u601d\u8003\u5757\u5df2\u663e\u793a",
    "thinking_hidden": "\u601d\u8003\u5757\u5df2\u9690\u85cf",
    "thinking_expand_hint": "\u601d\u8003 - \u6309 't' \u5c55\u5f00",

    # Search
    "search_title": "\u641c\u7d22\u5bf9\u8bdd",
    "search_esc_hint": "Esc \u5173\u95ed",
    "search_placeholder": "\u8f93\u5165\u641c\u7d22\u5173\u952e\u8bcd\u540e\u6309 Enter...",
    "search_no_results": "\u672a\u627e\u5230\u7ed3\u679c",
    "search_results_for": "\u6761\u7ed3\u679c\uff0c\u5173\u952e\u8bcd\uff1a",

    # Table headers
    "col_model": "\u6a21\u578b",
    "col_input_tokens": "\u8f93\u5165 Token",
    "col_output_tokens": "\u8f93\u51fa Token",
    "col_cache_read": "\u7f13\u5b58\u8bfb\u53d6",
    "col_cache_write": "\u7f13\u5b58\u5199\u5165",
    "col_est_cost": "\u9884\u4f30\u8d39\u7528",
    "col_percent": "%",
    "total": "\u5408\u8ba1",

    # Heatmap
    "heatmap_title": "\u4f1a\u8bdd\u6309\u5c0f\u65f6\u5206\u5e03\uff08\u672c\u5730\u65f6\u95f4\uff09",
    "heatmap_no_data": "\u6682\u65e0\u65f6\u6bb5\u6570\u636e",
    "hour_period_0": "\u51cc\u6668",
    "hour_period_6": "\u4e0a\u5348",
    "hour_period_12": "\u4e0b\u5348",
    "hour_period_18": "\u665a\u4e0a",
    "legend_none": "\u65e0",
    "legend_low": "\u4f4e",
    "legend_med": "\u4e2d",
    "legend_high": "\u9ad8",
    "legend_peak": "\u5cf0\u503c",

    # Chart
    "chart_no_data": "\u6682\u65e0\u6570\u636e",

    # Misc
    "all_data_refreshed": "\u6570\u636e\u5df2\u5237\u65b0",
    "worktree_tag": "\u5de5\u4f5c\u6811",
    "in_label": "\u8f93\u5165",
    "out_label": "\u8f93\u51fa",
}

# ---------------------------------------------------------------------------
# Translation registry
# ---------------------------------------------------------------------------

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": _EN,
    "zh": _ZH,
}
