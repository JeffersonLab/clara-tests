class tools {
    Package {
        ensure => installed,
    }

    package { [
        "git-all",
        "tig",
        "subversion",
    ]:
    }

    package { [
        "screen",
        "tmux",
    ]:
    }

    package { [
        "colordiff",
    ]:
    }
}
