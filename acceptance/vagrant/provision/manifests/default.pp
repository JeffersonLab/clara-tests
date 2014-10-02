class common {
    $private_ip = $hostname ? {
        'platform' => '10.11.1.100',
        'dpe1'     => '10.11.1.101',
        'dpe2'     => '10.11.1.102',
    }

    # Fix "localhost" IP in Java
    host {
        $hostname: ip => $private_ip
    }

    file { "/home/vagrant/clara":
        ensure => "directory",
        owner => "vagrant",
        group => "vagrant",
    }

    package { [
        "python-mock",
        "python-daemon",
    ]:
        ensure => latest,
    }

}

include common
include locales
include clara
include tools
include dotfiles
