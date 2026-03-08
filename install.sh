# Based on : https://github.com/andrewmcgr/klipper_tmc_autotune/blob/main/install.sh


#!/bin/bash

KLIPPER_PATH="${HOME}/klipper"
ESP_NEVERMORE_PATH="${HOME}/esphome-nevermore-controller"

if [[ -e ${KLIPPER_PATH}/klippy/plugins/ ]]; then
    KLIPPER_PLUGINS_PATH="${KLIPPER_PATH}/klippy/plugins/"
else
    KLIPPER_PLUGINS_PATH="${KLIPPER_PATH}/klippy/extras/"
fi

set -eu
export LC_ALL=C


function preflight_checks {
    if [ "$EUID" -eq 0 ]; then
        echo "[PRE-CHECK] This script must not be run as root!"
        exit 1
    fi

    if sudo systemctl list-units --full -all -t service --no-legend | grep -q 'klipper.service'; then
        echo "[PRE-CHECK] Klipper service found!"
    else
        echo "[ERROR] Klipper service not found, please install Klipper first!"
        exit 1
    fi

    # Try to determine the klippy virtual environment from the local Moonraker instance
    KLIPPY_PYTHON_PATH=$(curl http://localhost:7125/printer/info 2>&1 | grep -o '"python_path":"[^"]*' | grep -o '[^"]*$' || true)
    # Fall back to the default location
    KLIPPY_PYTHON_PATH=${KLIPPY_PYTHON_PATH:-"${HOME}/klippy-env/bin/python"}
    # Get the major Python version
    KLIPPY_PYTHON_VERSION=$("${KLIPPY_PYTHON_PATH}" -c 'import sys; print(sys.version_info.major)')

    if [[ ${KLIPPY_PYTHON_VERSION} -lt 3 ]]; then
        echo "[ERROR] Klipper must be using Python 3 - detected outdated Python 2"
        exit 1
    else
        echo "[PRE-CHECK] Klipper is using Python 3!"
    fi

    printf "\n\n"
}

function check_download {
    local esp_nevermore_dirname esp_nevermore_basename
    esp_nevermore_dirname="$(dirname "${ESP_NEVERMORE_PATH}")"
    esp_nevermore_basename="$(basename "${ESP_NEVERMORE_PATH}")"

    if [ ! -d "${ESP_NEVERMORE_PATH}" ]; then
        echo "[DOWNLOAD] Downloading esphome-nevermore-controller repository..."
        if git -C "${esp_nevermore_dirname}" clone https://github.com/martijnvanduijneveldt/esphome-nevermore-controller.git $esp_nevermore_basename; then
            chmod +x "${ESP_NEVERMORE_PATH}"/install.sh
            printf "[DOWNLOAD] Download complete!\n\n"
        else
            echo "[ERROR] Download of esphome-nevermore-controller git repository failed!"
            exit 1
        fi
    else
        printf "[DOWNLOAD] esphome-nevermore-controller repository already found locally. Continuing...\n\n"
    fi
}

function link_extension {
    echo "[INSTALL] Linking extension to Klipper..."
    rm -f ${KLIPPER_PLUGINS_PATH}/esphome_nevermore.py
    ln -srfn "${ESP_NEVERMORE_PATH}/__init__.py" "${KLIPPER_PLUGINS_PATH}/esphome_nevermore.py"

    echo "[INSTALL] Linking extension library folder to Klipper..."
    rm -f ${KLIPPER_PLUGINS_PATH}/esphome_nevermore_library
    ln -s "${ESP_NEVERMORE_PATH}/esphome_nevermore_library" "${KLIPPER_PLUGINS_PATH}/esphome_nevermore_library"
}


function install_dependencies {
    echo "Installing python dependencies... "
    "$KLIPPY_PYTHON_PATH" -m pip install -r "${ESP_NEVERMORE_PATH}/requirements.txt"
}

function restart_klipper {
    echo "[POST-INSTALL] Restarting Klipper..."
    sudo systemctl restart klipper
}


printf "\n======================================\n"
echo "- esphome-nevermore-controller install script -"
printf "======================================\n\n"


# Run steps
preflight_checks
check_download
link_extension
restart_klipper
install_dependencies