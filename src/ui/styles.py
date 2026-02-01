def get_stylesheet():
    return """
    QMainWindow {
        background-color: #f5f6fa;
    }
    
    QFrame#sidebar {
        background-color: #1a3a8a;
        min-width: 250px;
        max-width: 250px;
    }
    
    QPushButton#menu_button {
        background-color: transparent;
        color: #dcdde1;
        text-align: left;
        padding: 12px 20px;
        border: none;
        font-size: 14px;
        border-radius: 5px;
        margin: 2px 10px;
    }
    
    QPushButton#menu_button:hover {
        background-color: #353b48;
        color: white;
    }
    
    QPushButton#menu_button:checked {
        background-color: #0097e6;
        color: white;
    }
    
    QFrame#content_area {
        background-color: white;
        border-top-left-radius: 20px;
        margin: 10px;
    }
    
    QLabel#header_title {
        font-size: 24px;
        font-weight: bold;
        color: #2f3640;
    }
    
    QLineEdit {
        padding: 10px;
        border: 1px solid #dcdde1;
        border-radius: 5px;
        background-color: white;
    }
    
    QPushButton#primary_button {
        background-color: #0097e6;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
    }
    
    QPushButton#primary_button:hover {
        background-color: #00a8ff;
    }
    
    QTableWidget {
        border: none;
        background-color: white;
        alternate-background-color: #f5f6fa;
    }
    
    QHeaderView::section {
        background-color: #f5f6fa;
        padding: 5px;
        border: none;
        font-weight: bold;
    }
    
    /* RTL Support */
    *[layoutDirection="1"] {
        text-align: right;
    }
    """
