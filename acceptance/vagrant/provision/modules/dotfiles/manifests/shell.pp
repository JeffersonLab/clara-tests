class dotfiles::shell {

    package { ["zsh", "ncurses-term"]:
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
        require => Package["zsh"]
    }

    file { "/home/vagrant/.profile":
        source => "puppet:///modules/dotfiles/profile",
    }

    file { "/home/vagrant/.zprofile":
        source => "puppet:///modules/dotfiles/zprofile",
    }

    file { "/home/vagrant/.zshrc":
        source => "puppet:///modules/dotfiles/zshrc",
    }

    file { "/home/vagrant/.zlogout":
        source => "puppet:///modules/dotfiles/zlogout",
    }
}
