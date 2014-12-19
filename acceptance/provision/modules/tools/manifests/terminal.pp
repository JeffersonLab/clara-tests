class tools::terminal {
    Package {
        ensure => installed,
    }

    File {
        ensure => present,
        owner => "vagrant",
        group => "vagrant",
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

    file { "/home/vagrant/.tmux.conf":
        source => "puppet:///modules/tools/tmux.conf",
    }

    file { "/home/vagrant/.screenrc":
        source => "puppet:///modules/tools/screenrc",
    }

    file { "/home/vagrant/.colordiffrc":
        source => "puppet:///modules/tools/colordiffrc",
    }
}
