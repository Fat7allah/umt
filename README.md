# UNEM Management System

A comprehensive management system for UNEM (Union Nationale de l'Enseignement au Maroc) built with Frappe v14.

## Features

- Multi-language support (Arabic, French)
- Member management
- Membership card system
- UNEM and Mutual structure management
- Financial operations tracking
- Academic year management

## Installation

1. Install Frappe Bench and create a new site
```bash
bench new-site unem.local
```

2. Get the app from GitHub
```bash
bench get-app umt https://github.com/unem/umt
```

3. Install the app on your site
```bash
bench --site unem.local install-app umt
```

## Requirements

- Frappe v14+
- Python 3.10+
- MariaDB 10.6+
- Additional Python packages (see requirements.txt)

## Configuration

1. Set up languages in System Settings
2. Configure Academic Year settings
3. Set up user roles and permissions

## License

MIT
