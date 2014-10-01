class dotfiles::terminal {
    File {
        ensure => present,
        owner => "vagrant",
        group => "vagrant",
    }

    file { "/home/vagrant/.tmux.conf":
        source => "puppet:///modules/dotfiles/tmux.conf",
    }

    file { "/home/vagrant/.screenrc":
        source => "puppet:///modules/dotfiles/screenrc",
    }

    file { "/home/vagrant/.colordiffrc":
        source => "puppet:///modules/dotfiles/colordiffrc",
    }
}
