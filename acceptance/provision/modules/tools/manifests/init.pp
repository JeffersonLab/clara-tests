class tools {
    Package {
        ensure => installed,
    }

    package { [
        "git",
        "git-svn",
        "tig",
        "subversion",
    ]:
    }

    package { [
        "vim-nox",
        "emacs24-nox",
        "screen",
        "tmux",
    ]:
    }

    package { [
        "colordiff",
        "cdargs",
        "ranger",
    ]:
    }
}
