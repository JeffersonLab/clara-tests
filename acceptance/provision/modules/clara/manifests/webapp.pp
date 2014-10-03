class clara::webapp {
    Package {
        ensure => latest,
    }

    package { [
        "curl",
        "libpq-dev",
        "nodejs",
    ]:
    }

    exec { 'install-rvm':
        command => "/bin/su -l --command='curl -sSL https://get.rvm.io | bash -s stable --ignore-dotfiles' vagrant",
        creates => "/home/vagrant/.rvm/bin/rvm",
        require => Package['curl'],
        logoutput => true,
    }

    exec {'install-ruby':
        command =>"/bin/su -l --command='rvm install 2.1.2' vagrant",
        require => [ Exec['install-rvm'], File['/home/vagrant/.profile'] ],
        timeout => 1800,
        logoutput => true,
    }
}
