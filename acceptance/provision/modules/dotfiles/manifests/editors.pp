class dotfiles::editors {
    File {
        ensure => present,
        owner  => "vagrant",
        group  => "vagrant",
    }

    file { "/home/vagrant/.vimrc":
        source => "puppet:///modules/dotfiles/vimrc",
    }
}
