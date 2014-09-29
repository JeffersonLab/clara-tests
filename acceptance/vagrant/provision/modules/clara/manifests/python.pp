class clara::python {
    Package {
        ensure => latest,
    }

    package { [
        "python-zmq",
    ]:
    }
}
