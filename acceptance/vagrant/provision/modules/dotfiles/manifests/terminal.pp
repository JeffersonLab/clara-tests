class dotfiles::terminal {
    File {
        ensure => present,
    }

    file { "/home/vagrant/.tmux.conf":
        source => "puppet:///modules/dotfiles/tmux.conf",
    }

    file { "/home/vagrant/.screenrc":
        source => "puppet:///modules/dotfiles/screenrc",
    }
}
