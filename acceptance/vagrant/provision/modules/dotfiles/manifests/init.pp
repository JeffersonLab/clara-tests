class dotfiles {
    include dotfiles::shell
    include dotfiles::base

    Class['dotfiles::shell'] -> Class['dotfiles::base']
}
