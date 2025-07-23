#!/bin/bash
# Shell script to run Django server for cross-device access
# Usage: bash run_server.sh or ./run_server.sh

# Ensure script is executable: chmod +x run_server.sh

echo -e "\e[32mFinance Tracker - Multi-Device Server Launcher\e[0m"
echo -e "\e[32m================================================\e[0m"

# Get current directory
CURR_DIR=$(pwd)
echo -e "\e[36mCurrent directory: $CURR_DIR\e[0m"

# Check if we're in the project root or need to change directory
if [ ! -f "./manage.py" ]; then
    if [ -f "./finance_tracker/manage.py" ]; then
        cd ./finance_tracker
        echo -e "\e[36mChanged directory to: $(pwd)\e[0m"
    else
        echo -e "\e[31mError: Could not find manage.py. Please run this script from the project root directory.\e[0m"
        exit 1
    fi
fi

# Display header
echo "====================================================="
echo "Starting Finance Tracker Server for Mobile Access"
echo "====================================================="
echo

# Check if we're on macOS or Linux and show IP information accordingly
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Network Information for Mobile Access (macOS):"
    echo "-----------------------------------------------------"
    ip_addr=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | cut -d\  -f2 | head -n 1)
    echo "Your IP address: $ip_addr"
else
    echo "Network Information for Mobile Access (Linux):"
    echo "-----------------------------------------------------" 
    ip_addr=$(hostname -I | awk '{print $1}')
    echo "Your IP address: $ip_addr"
fi

echo
echo "Mobile Access URL: http://$ip_addr:8000"
echo
echo "Copy this URL to access from your mobile device"
echo "when connected to the same WiFi network."
echo "====================================================="
echo

echo -e "\e[36mUpdating settings.py with CSRF trusted origins...\e[0m"
SETTINGS_PATH="./finance_tracker/settings.py"

# Check if settings.py exists
if [ ! -f "$SETTINGS_PATH" ]; then
    SETTINGS_PATH="./settings.py"
    if [ ! -f "$SETTINGS_PATH" ]; then
        echo -e "\e[31mError: Could not find settings.py\e[0m"
        exit 1
    fi
fi

# Read settings.py content
SETTINGS_CONTENT=$(cat "$SETTINGS_PATH")

# Check if settings already has the IP address
if [[ "$SETTINGS_CONTENT" != *"CSRF_TRUSTED_ORIGINS += ['http://$ip_addr:8000']"* ]]; then
    # Find the CSRF_TRUSTED_ORIGINS line and uncomment/modify it
    if [[ "$SETTINGS_CONTENT" == *"# CSRF_TRUSTED_ORIGINS += ['http://"* ]]; then
        # Replace the commented line
        sed -i.bak "s|# CSRF_TRUSTED_ORIGINS += \['http://.*:8000'\]|CSRF_TRUSTED_ORIGINS += ['http://$ip_addr:8000']|g" "$SETTINGS_PATH"
    else
        # Add the line directly after CSRF_TRUSTED_ORIGINS = [...]
        sed -i.bak "/CSRF_TRUSTED_ORIGINS = \[/a\\
CSRF_TRUSTED_ORIGINS += ['http://$ip_addr:8000']" "$SETTINGS_PATH"
    fi
    
    echo -e "\e[32m  Added $ip_addr to CSRF_TRUSTED_ORIGINS\e[0m"
else
    echo -e "\e[32m  $ip_addr already in CSRF_TRUSTED_ORIGINS\e[0m"
fi

# Clean up backup file
rm -f "$SETTINGS_PATH.bak"

echo ""
echo -e "\e[36mStarting server on 0.0.0.0:8000...\e[0m"
echo -e "\e[36m-------------------------------------\e[0m"
echo -e "\e[33mFinance Tracker will be accessible at:\e[0m"
echo -e "\e[33m  Local:            http://127.0.0.1:8000\e[0m"
echo -e "\e[33m  On Your Network:  http://$ip_addr:8000\e[0m"
echo -e "\e[36m-------------------------------------\e[0m"
echo -e "\e[31mPress Ctrl+C to stop the server\e[0m"
echo ""

# Start the server
python manage.py runserver 0.0.0.0:8000 