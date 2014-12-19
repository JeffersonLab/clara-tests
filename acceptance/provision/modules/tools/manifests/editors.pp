class tools::editors {
    package { [
        "vim-nox",
        "emacs24-nox",
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
