import sys
from plugin.wrapper import EvmLoaderProgram

program = EvmLoaderProgram()
# lamports, space, ether, signer_key, program_key, system_program_key
program.createAccount(1000, 1000, sys.argv[0], sys.argv[1], sys.argv[2], sys.argv[3])
