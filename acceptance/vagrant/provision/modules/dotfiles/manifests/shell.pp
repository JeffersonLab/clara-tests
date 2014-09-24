class dotfiles::shell {

    package { "zsh":
        ensure => installed,
    }

    user { "vagrant":
        shell   => "/bin/zsh",
        require => Package["zsh"],
    }
}
