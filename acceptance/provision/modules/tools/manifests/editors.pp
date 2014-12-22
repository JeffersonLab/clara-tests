class tools::editors {
    package { [
        "vim-gtk",
        "emacs24",
    ]:
        ensure => installed,
    }

    File {
        ensure => present,
        owner  => "vagrant",
        group  => "vagrant",
    }

    file { "/home/vagrant/.vimrc":
        source => "puppet:///modules/tools/vimrc",
    }
}
