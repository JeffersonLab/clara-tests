class devtools {
    Package {
        ensure => installed,
    }

    package { [
        "openjdk-7-jdk",
        "ant",
    ]:
    }

    package { [
        "bundler",
    ]:
    }
}

# Fix "localhost" IP in Java
class network {
    $private_ip = $hostname ? {
        'platform' => '10.11.1.100',
        'dpe1'     => '10.11.1.101',
        'dpe2'     => '10.11.1.102',
    }

    host {
        $hostname: ip => $private_ip
    }
}

include devtools
include network
include dotfiles
