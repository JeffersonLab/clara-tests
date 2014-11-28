class clara::webapp {
    Package {
        ensure => latest,
    }

    package { [
        "curl",
        "gnupg",
        "libpq-dev",
        "nodejs",
    ]:
    }

    exec { 'rvm-key':
        command   => "/bin/su -l --command='gpg --keyserver hkp://keys.gnupg.net --recv-keys D39DC0E3' vagrant",
        require   => Package['gnupg'],
        unless    => "/bin/su -l --command 'gpg --list-keys | grep -q D39DC0E3' vagrant",
        logoutput => true,
    }

    exec { 'install-rvm':
        command => "/bin/su -l --command='curl -sSL https://get.rvm.io | bash -s stable --ignore-dotfiles' vagrant",
        creates => "/home/vagrant/.rvm/bin/rvm",
        require => [ Exec['rvm-key'], Package['curl'] ],
        logoutput => true,
    }

    exec {'install-ruby':
        command =>"/bin/su -l --command='rvm install 2.1.2' vagrant",
        require => [ Exec['install-rvm'], File['/home/vagrant/.profile'] ],
        timeout => 1800,
        logoutput => true,
    }
}
