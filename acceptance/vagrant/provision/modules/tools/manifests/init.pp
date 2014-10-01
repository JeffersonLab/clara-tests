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
