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
}
