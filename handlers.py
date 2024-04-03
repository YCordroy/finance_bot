from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

import new_func as func

handlers = [
    ConversationHandler(
        entry_points=[CommandHandler('add', func.add)],
        states={
            func.CATEGORY: [MessageHandler(~filters.COMMAND, func.set_category)],
            func.PRICE: [MessageHandler(~filters.COMMAND, func.set_price)],
            func.COMMENT: [
                MessageHandler(~filters.COMMAND, func.set_comment),
                CommandHandler('skip', func.save)
            ]
        },
        fallbacks=[CommandHandler('end', func.end_add)]
    ),
    CallbackQueryHandler(func.change_category_keyboard, 'change_category'),
    CallbackQueryHandler(func.re_set_category, r're_set_category_\d+'),
    CallbackQueryHandler(func.back, 'back'),
    CallbackQueryHandler(func.keyboard_for_del, 'delete_message'),
    CallbackQueryHandler(func.confirm_del, 'confirm_del'),
    CallbackQueryHandler(func.select_date, r'change_date_(\d{1,2})_(\d{4})'),
    CallbackQueryHandler(func.change_date, r'calendar_(\d{4})-(\d{2})-(\d{2})'),
    CommandHandler('report', func.get_report),
    CallbackQueryHandler(func.report_get_date, r'report_get_(\d{1,2})_(\d{4})'),
    CallbackQueryHandler(func.report_select_date, r'report_date_(\d{4})-(\d{2})-(\d{2})'),
    CallbackQueryHandler(func.report_get_user, 'report_get_users'),
    CallbackQueryHandler(func.report_select_user, r'get_user_(\d+|all)'),
    CallbackQueryHandler(func.report_get_report, 'report_get_report'),
    CallbackQueryHandler(func.report_stop_report, 'stop_report'),
    MessageHandler(filters.ALL, func.delete_user_message)
]
