class clara {
    include clara::java
    include clara::python
    if $hostname =~ /^platform/ {
        include clara::webapp
    }
}
