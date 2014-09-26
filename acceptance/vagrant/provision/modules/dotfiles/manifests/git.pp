class dotfiles::git {
    File {
        ensure => present,
    }

    file { "/home/vagrant/.config":
        ensure => "directory",
    }

    file { "/home/vagrant/.config/git":
        ensure => "directory",
    }

    file { "/home/vagrant/.config/git/config":
        source => "puppet:///modules/dotfiles/git-config",
    }

    file { "/home/vagrant/.config/git/attributes":
        source => "puppet:///modules/dotfiles/git-attributes",
    }

    file { "/home/vagrant/.config/git/ignore":
        source => "puppet:///modules/dotfiles/git-ignore",
    }
}
