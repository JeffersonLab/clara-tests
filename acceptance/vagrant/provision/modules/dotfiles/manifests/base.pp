class dotfiles::base {
    $profile = "/home/vagrant/.profile"
    $zprofile = "/home/vagrant/.zprofile"
    $zshrc = "/home/vagrant/.zshrc"
    $zlogout = "/home/vagrant/.zlogout"

    File {
        mode => 0600,
        ensure => present,
        owner => "vagrant",
        group => "vagrant",
    }

    file { $profile:
        source => "puppet:///modules/dotfiles/profile",
    }

    file { $zprofile:
        source => "puppet:///modules/dotfiles/zprofile",
    }

    file { $zshrc:
        source => "puppet:///modules/dotfiles/zshrc",
    }

    file { $zlogout:
        source => "puppet:///modules/dotfiles/zlogout",
    }
}
