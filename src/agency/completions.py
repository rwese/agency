"""Shell completion scripts for agency."""

BASH_COMPLETION = """# bash completion for agency
_agency_completions()
{
    local cur prev words cword
    _init_completion || return

    case "${words[1]}" in
        init)
            _filedir
            ;;
        session)
            case "${words[2]}" in
                start)
                    _filedir
                    ;;
                stop|kill)
                    COMPREPLY=($(compgen -W "$(agency session list 2>/dev/null | grep "^agency-" | sed 's/agency-//')" -- "${cur}"))
                    ;;
                windows)
                    case "${words[3]}" in
                        send|run)
                            ;;
                        *)
                            COMPREPLY=($(compgen -W "list send new run" -- "${cur}"))
                            ;;
                    esac
                    ;;
                *)
                    COMPREPLY=($(compgen -W "start stop kill resume attach list members windows" -- "${cur}"))
                    ;;
            esac
            ;;
        tasks)
            case "${words[2]}" in
                add|assign|complete|approve|reject|reopen|update|show|delete|depends)
                    ;;
                *)
                    COMPREPLY=($(compgen -W "list add show assign depends complete approve reject reopen update delete history" -- "${cur}"))
                    ;;
            esac
            ;;
        *)
            COMPREPLY=($(compgen -W "init session tasks heartbeat audit templates completions" -- "${cur}"))
            ;;
    esac
}

complete -F _agency_completions agency
"""

ZSH_COMPLETION = """# zsh completion for agency
_agency() {
    local -a commands
    commands=(
        "init:Create a new project"
        "session:Session management"
        "tasks:Task management"
        "heartbeat:Heartbeat process management"
        "audit:Audit trail management"
        "templates:List available templates"
        "completions:Print shell completion"
    )

    local -a session_commands
    session_commands=(
        "start:Start the session"
        "stop:Stop session gracefully"
        "kill:Force kill session"
        "resume:Resume halted session"
        "attach:Attach to session"
        "list:List sessions"
        "members:Show session members"
        "windows:Window operations"
    )

    local -a session_windows_commands
    session_windows_commands=(
        "list:List windows"
        "send:Send keys to window"
        "new:Create new window"
        "run:Run command in window"
    )

    _arguments -C \\
        '1: :->command' \\
        '*: :->args'

    case "$state" in
        command)
            _describe 'command' commands
            ;;
        args)
            case "$words[1]" in
                init)
                    _arguments '*:directory:_files -/'
                    ;;
                session)
                    case "$words[2]" in
                        windows)
                            case "$words[3]" in
                                send|run)
                                    ;;
                                *)
                                    _describe 'window-command' session_windows_commands
                                    ;;
                            esac
                            ;;
                        *)
                            _describe 'session-command' session_commands
                            ;;
                    esac
                    ;;
                tasks)
                    local -a task_commands
                    task_commands=(
                        "list:List tasks"
                        "add:Add task"
                        "show:Show task"
                        "assign:Assign task"
                        "depends:Manage dependencies"
                        "complete:Complete task"
                        "approve:Approve task"
                        "reject:Reject task"
                        "reopen:Reopen task"
                        "update:Update task"
                        "delete:Delete task"
                        "history:Show history"
                    )
                    _describe 'task-command' task_commands
                    ;;
            esac
            ;;
    esac
}

compdef _agency agency
"""

FISH_COMPLETION = """# fish completion for agency
# Main commands
complete -c agency -n '__fish_use_subcommand' -a 'init' -d 'Create a new project'
complete -c agency -n '__fish_use_subcommand' -a 'session' -d 'Session management'
complete -c agency -n '__fish_use_subcommand' -a 'tasks' -d 'Task management'
complete -c agency -n '__fish_use_subcommand' -a 'heartbeat' -d 'Heartbeat process'
complete -c agency -n '__fish_use_subcommand' -a 'audit' -d 'Audit trail'
complete -c agency -n '__fish_use_subcommand' -a 'templates' -d 'List templates'
complete -c agency -n '__fish_use_subcommand' -a 'completions' -d 'Print completion'

# Session subcommands
complete -c agency -n '__fish_seen_subcommand_from session' -a 'start' -d 'Start session'
complete -c agency -n '__fish_seen_subcommand_from session' -a 'stop' -d 'Stop session'
complete -c agency -n '__fish_seen_subcommand_from session' -a 'kill' -d 'Kill session'
complete -c agency -n '__fish_seen_subcommand_from session' -a 'resume' -d 'Resume session'
complete -c agency -n '__fish_seen_subcommand_from session' -a 'attach' -d 'Attach to session'
complete -c agency -n '__fish_seen_subcommand_from session' -a 'list' -d 'List sessions'
complete -c agency -n '__fish_seen_subcommand_from session' -a 'members' -d 'Show members'
complete -c agency -n '__fish_seen_subcommand_from session' -a 'windows' -d 'Window operations'

# Session windows subcommands
complete -c agency -n '__fish_seen_subcommand_from session; and __fish_seen_subcommand_from windows' -a 'list' -d 'List windows'
complete -c agency -n '__fish_seen_subcommand_from session; and __fish_seen_subcommand_from windows' -a 'send' -d 'Send keys'
complete -c agency -n '__fish_seen_subcommand_from session; and __fish_seen_subcommand_from windows' -a 'new' -d 'New window'
complete -c agency -n '__fish_seen_subcommand_from session; and __fish_seen_subcommand_from windows' -a 'run' -d 'Run command'

# Tasks subcommands
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'list' -d 'List tasks'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'add' -d 'Add task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'show' -d 'Show task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'assign' -d 'Assign task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'depends' -d 'Manage dependencies'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'complete' -d 'Complete task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'approve' -d 'Approve task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'reject' -d 'Reject task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'reopen' -d 'Reopen task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'update' -d 'Update task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'delete' -d 'Delete task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'history' -d 'Show history'
"""


def get_completion_script(shell: str) -> str:
    """Get the completion script for a shell."""
    if shell == "bash":
        return BASH_COMPLETION
    elif shell == "zsh":
        return ZSH_COMPLETION
    elif shell == "fish":
        return FISH_COMPLETION
    else:
        raise ValueError(f"Unknown shell: {shell}")
