class clara::cpp {
    Package {
        ensure => latest,
    }

    package { [
        "build-essential",
        "g++",
        "cmake",
    ]:
    }

    package { [
        "libexpat1-dev",
    ]:
    }

    package { [
        "libzmq3-dev",
        "libprotobuf-dev",
        "protobuf-compiler",
    ]:
    }
}
