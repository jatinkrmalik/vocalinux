# Phase: verify and welcome.
[[ "$RUN_TESTS" == "yes" ]] && run_tests
verify_installation
print_welcome_message $?
