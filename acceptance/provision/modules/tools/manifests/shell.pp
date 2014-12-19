class tools::shell {

    package { [
        "zsh",
        "ncurses-term",
    ]:
        ensure => installed,
    }

    user { "vagrant":
        shell   => "/bin/zsh",
        require => Package["zsh"],
    }

    File {
        mode => 0600,
        ensure => present,
        owner => "vagrant",
        group => "vagrant",
    }

    file { "/home/vagrant/bin":
        mode => 0700,
        ensure => "directory",
    }

    file { "/home/vagrant/.profile":
        source => "puppet:///modules/tools/profile",
    }

    file { "/home/vagrant/.zprofile":
        source => "puppet:///modules/tools/zprofile",
    }

    file { "/home/vagrant/.zshrc":
        source => "puppet:///modules/tools/zshrc",
    }

    file { "/home/vagrant/.zlogout":
        source => "puppet:///modules/tools/zlogout",
    }
}
