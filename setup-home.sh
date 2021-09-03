#! /bin/bash
set -ex

SELF_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CONFIG_DIR="$SELF_DIR"

make_dir() {
    mkdir -p $1
    sudo chmod 755 $1
}

link_files() {
    trap "$(shopt -p extglob)" RETURN
    shopt -s nullglob

    local base=$1
    local dst=$2
    local prefix=${3:-}

    echo "Link files from $base to $dst"
    make_dir "$dst"
    for dot in $base/*; do
        local tgt=$dst/$prefix${dot##*/}
        if [[ -d "$dot" ]]; then
            link_files "$dot" "$tgt"
        else
            echo "Link $dot -> $tgt"
            ln -sfn $(realpath $dot) "$tgt"
        fi
    done
}

# per user configs
config_user() {
    local TARGET_USER=$1
    local TARGET_GROUP=$(id -gn $TARGET_USER)
    local TARGET_HOME=$(eval echo "~$TARGET_USER")

    if [[ -f $TARGET_HOME/.setup-done ]]; then
        return
    fi

    echo "Configuring $TARGET_USER"

    echo "Redirect cache to /data"
    local mount_unit=$(systemd-escape --path --suffix=mount $TARGET_HOME/.cache)
    cat > /etc/systemd/user/$mount_unit <<EOF
[Unit]
Description=Bind $TARGET_HOME/.cache to /data/cache/$TARGET_USER

[Mount]
What=/data/cache/$TARGET_USER
Where=$TARGET_HOME/.cache
Type=none
Options=bind

[Install]
WantedBy=default.target
EOF
    sudo -u $TARGET_USER systemctl daemon-reload --user && sudo -u $TARGET_USER systemctl --user enable --now $mount_unit

    echo "Setting default shell to zsh"
    sudo chsh -s /usr/bin/zsh $TARGET_USER

    echo "Docker access"
    sudo usermod -aG docker $TARGET_USER

    echo "NodeJS"
    export NVM_DIR=$TARGET_HOME/.local/share/nvm
    # tell nvm to not touch our zshrc
    export PROFILE=/dev/null
    export NODE_VERSION=lts/*
    mkdir -p $NVM_DIR
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash

    # dotfiles
    echo "Linking dotfiles"
    make_dir $TARGET_HOME/.local
    link_files $CONFIG_DIR/dotfiles/home $TARGET_HOME "."
    ln -nsf $CONFIG_DIR/dotfiles/scripts $TARGET_HOME/.local/bin

    # common directories
    make_dir $TARGET_HOME/tools
    make_dir $TARGET_HOME/downloads
    make_dir $TARGET_HOME/buildbed

    # fix mounting point
    if [[ -d $TARGET_HOME/my_mounting_point ]]; then
        sudo umount $TARGET_HOME/my_mounting_point
    fi

    # fix permission
    echo "Fixing permission"
    sudo chown -R $TARGET_USER:$TARGET_GROUP $TARGET_HOME

    # initialize vim as if on first login
    sudo su --login $TARGET_USER <<EOSU
zsh --login -c "umask 022 && source \$HOME/.zshrc && echo Initialized zsh" > $TARGET_HOME/zsh-setup.log &
nvim -es -u $TARGET_HOME/.config/nvim/init.vim -i NONE -c "PlugInstall" -c "qa" > $TARGET_HOME/vim-setup.log &
wait
EOSU

    date > $TARGET_HOME/.setup-done
}

sudo git -C $SELF_DIR pull

for user in "$@"
do
    config_user "$user"
done
